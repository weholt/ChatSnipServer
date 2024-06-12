import logging
import time

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)
from rest_framework import status, viewsets
from rest_framework.response import Response

from .forms import ChatSnipProfileForm
from .models import Chat, ChatSnipProfile, CodeFragment
from .serializers import ChatSerializer, CodeFragmentSerializer
from .services import (
    check_duplicate_chat_content,
    check_duplicate_code_fragment,
    compose_chat_view,
    compose_source_code_view,
    get_or_create_chat,
    get_pretty_date,
    parse_source_code_fragments,
    save_code_fragment,
)

logger = logging.getLogger(__name__)


class ChatViewSet(viewsets.ModelViewSet):
    """API endpoint for Chat."""

    queryset = Chat.objects.all()
    serializer_class = ChatSerializer

    def create(self, request, *args, **kwargs):
        api_key = request.data.get("apiKey")
        logger.debug(f"Received API Key: {api_key}")
        if not api_key:
            logger.debug("API key missing.")
            return Response({"status": "API key missing."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            profile = ChatSnipProfile.objects.get(api_key=api_key)
        except ChatSnipProfile.DoesNotExist:
            logger.debug("Invalid API key.")
            return Response({"status": "Invalid API key."}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        logger.debug(f"Received data: {data}")
        identifier = data.get("chatId")
        content = data.get("content")

        with open(f"dump_{int(time.time())}", "w", encoding="utf-8") as f:
            f.write(content)

        chat_name = data.get("name", get_pretty_date())

        if chat := Chat.objects.filter(unique_identifier=identifier, user=profile.user).first():
            if check_duplicate_chat_content(chat, content):
                logger.debug("Duplicate chat content.")
                return Response({"status": "Duplicate content."}, status=status.HTTP_208_ALREADY_REPORTED)
        else:
            chat = get_or_create_chat(identifier, chat_name, profile.user)
            chat.content = content
            chat.save()

        # import pprint
        # pprint.pprint(parse_source_code_fragments(content)[0])

        for filename, source_code in parse_source_code_fragments(content):
            save_code_fragment(chat, filename, source_code)

        return Response({"status": "Chat saved."})


class CodeFragmentViewSet(viewsets.ModelViewSet):
    """API endpoint for CodeFragment."""

    queryset = CodeFragment.objects.all()
    serializer_class = CodeFragmentSerializer

    def create(self, request, *args, **kwargs):
        api_key = request.data.get("apiKey")
        logger.debug(f"Received API Key: {api_key}")
        if not api_key:
            logger.debug("API key missing.")
            return Response({"status": "API key missing."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            profile = ChatSnipProfile.objects.get(api_key=api_key)
        except ChatSnipProfile.DoesNotExist:
            logger.debug("Invalid API key.")
            return Response({"status": "Invalid API key."}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        logger.debug(f"Received data: {data}")
        chat = Chat.objects.get(id=data.get("chat_id"))
        if check_duplicate_code_fragment(chat, data.get("filename"), data.get("source_code")):
            logger.debug("Duplicate code fragment content.")
            return Response({"status": "Duplicate content."}, status=status.HTTP_400_BAD_REQUEST)
        code_fragment = save_code_fragment(chat, data.get("filename"), data.get("source_code"), data.get("programming_language"))
        return Response({"status": "Code fragment saved."})


class ChatListView(LoginRequiredMixin, ListView):
    """View to list all chats."""

    model = Chat
    template_name = "chatsnip/chat_list.html"
    context_object_name = "chats"


class ChatDetailView(LoginRequiredMixin, DetailView):
    """View to display details of a single chat."""

    model = Chat
    template_name = "chatsnip/chat_detail.html"
    context_object_name = "chat"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(compose_chat_view(self.object))
        return context


class ChatCreateView(LoginRequiredMixin, CreateView):
    """View to create a new chat."""

    model = Chat
    template_name = "chatsnip/chat_form.html"
    fields = ["name", "content", "tags"]
    success_url = reverse_lazy("chatsnip:chat_list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        if check_duplicate_chat_content(form.instance.unique_identifier, form.instance.content):
            return JsonResponse({"status": "Duplicate content."}, status=400)
        form.save()
        return JsonResponse({"status": "Chat saved."})


class ChatUpdateView(LoginRequiredMixin, UpdateView):
    """View to update an existing chat."""

    model = Chat
    template_name = "chatsnip/chat_form.html"
    fields = ["name", "content", "tags"]
    success_url = reverse_lazy("chatsnip:chat_list")


class ChatDeleteView(LoginRequiredMixin, DeleteView):
    """View to delete an existing chat."""

    model = Chat
    template_name = "chatsnip/chat_confirm_delete.html"
    success_url = reverse_lazy("chatsnip:chat_list")


class CodeFragmentListView(LoginRequiredMixin, ListView):
    """View to list all code fragments."""

    model = CodeFragment
    template_name = "chatsnip/codefragment_list.html"
    context_object_name = "code_fragments"


class CodeFragmentDetailView(LoginRequiredMixin, DetailView):
    """View to display details of a single code fragment."""

    model = CodeFragment
    template_name = "chatsnip/codefragment_detail.html"
    context_object_name = "code_fragment"


class CodeFragmentCreateView(LoginRequiredMixin, CreateView):
    """View to create a new code fragment."""

    model = CodeFragment
    template_name = "chatsnip/codefragment_form.html"
    fields = ["chat", "filename", "programming_language", "source_code"]
    success_url = reverse_lazy("chatsnip:codefragment_list")

    def form_valid(self, form):
        if check_duplicate_code_fragment(form.instance.chat, form.instance.filename, form.instance.source_code):
            return JsonResponse({"status": "Duplicate content."}, status=400)
        form.save()
        return JsonResponse({"status": "Code fragment saved."})


class CodeFragmentUpdateView(LoginRequiredMixin, UpdateView):
    """View to update an existing code fragment."""

    model = CodeFragment
    template_name = "chatsnip/codefragment_form.html"
    fields = ["filename", "programming_language", "source_code", "selected"]
    success_url = reverse_lazy("chatsnip:codefragment_list")


class CodeFragmentDeleteView(LoginRequiredMixin, DeleteView):
    """View to delete an existing code fragment."""

    model = CodeFragment
    template_name = "chatsnip/codefragment_confirm_delete.html"
    success_url = reverse_lazy("chatsnip:codefragment_list")


class ExtensionDetailView(TemplateView):
    """View to display details and installation instructions for the Chrome extension."""

    template_name = "chatsnip/extension_detail.html"


@login_required
def regenerate_api_key(request):
    profile = request.user.chatsnipprofile
    profile.regenerate_api_key()
    return redirect("chatsnip:profile")


class ChatSnipProfileUpdateView(LoginRequiredMixin, UpdateView):
    """View to update the ChatSnip profile."""

    model = ChatSnipProfile
    form_class = ChatSnipProfileForm
    template_name = "chatsnip/profile_form.html"
    success_url = reverse_lazy("chatsnip:profile")

    def get_object(self):
        return self.request.user.chatsnipprofile

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
