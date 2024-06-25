import json
import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
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
from pygments.formatters import HtmlFormatter

from .forms import ChatSnipProfileForm
from .models import Chat, ChatSnipProfile, CodeFragment
from .serializers import ChatSerializer, CodeFragmentSerializer
from .services import (
    check_duplicate_chat_content,
    check_duplicate_code_fragment,
    compose_chat_view,
    compose_source_code_view,
    download_and_save_image,
    get_or_create_chat,
    get_pretty_date,
    parse_source_code_fragments,
    save_code_fragment,
)

logger = logging.getLogger(__name__)
formatter = HtmlFormatter(style='colorful')
pygments_css = formatter.get_style_defs('.highlight')

class ChatViewSet(viewsets.ModelViewSet):
    """API endpoint for Chat."""

    queryset = Chat.objects.all()
    serializer_class = ChatSerializer

    def create(self, request, *args, **kwargs):
        api_key = request.data.get("apiKey")
        logger.debug(f"Received API Key: {api_key}")
        if not api_key:
            logger.debug("API key missing.")
            return Response(
                {"status": "API key missing."}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            profile = ChatSnipProfile.objects.get(api_key=api_key)
        except ChatSnipProfile.DoesNotExist:
            logger.debug("Invalid API key.")
            return Response(
                {"status": "Invalid API key."}, status=status.HTTP_403_FORBIDDEN
            )

        data = request.data
        identifier = data.get("chatId")
        json_data = data.get("content")
        markdown = data.get('markdown', "")
        chat_name = data.get("chatName", get_pretty_date())
        images = [element for element in json_data if "src" in element]        
        code_samples = [element for element in json_data if "language" in element]
        saved = []
        unchanged = []
        import pprint
        pprint.pprint(json_data)

        if chat := Chat.objects.filter(
            unique_identifier=identifier, user=profile.user
        ).first():
            if check_duplicate_chat_content(chat, json.dumps(json_data)) and chat.images_downloaded:
                logger.debug("Duplicate chat content.")
                return Response(
                    {"status": "Duplicate content."},
                    status=status.HTTP_208_ALREADY_REPORTED,
                )
        else:
            chat = get_or_create_chat(identifier, chat_name, profile.user)
            chat.markdown = markdown
            chat.json_data = json_data
            if not images:
                chat.images_downloaded = True
            saved.append('chat')
            chat.save()

        if images:
            image_source_replacement = {}
            for image in images:
                result = download_and_save_image(
                    chat, image.get("src"), title=None, description=image.get("content")
                )
                if not result.get('status') and result.get("status_code", 200) == 403:
                    return Response({"status": "Chat saved, but images could not be downloaded. Refresh page and try again."})

                if "image" in result:
                    image_source_replacement[image.get("src")] = result.get('image').image.url

            saved.append('images')
                            
            if image_source_replacement:
                for original_source, new_source in image_source_replacement.items():
                    chat.markdown = chat.markdown.replace(original_source, new_source)
                    chat.json_data = json.loads(json.dumps(chat.json_data).replace(original_source, new_source))
                chat.save()

            if not chat.images_downloaded:
                chat.images_downloaded = True
                chat.save()
            
        for code_sample in code_samples:
            if save_code_fragment(chat, filename=code_sample.get("filename"), content=code_sample.get("content"), language=code_sample.get("language")):
                if not 'code' in saved:
                    saved.append('code')

        return Response({"status": f"Process done. Saved {' & '.join(saved)}."})


class CodeFragmentViewSet(viewsets.ModelViewSet):
    """API endpoint for CodeFragment."""

    queryset = CodeFragment.objects.all()
    serializer_class = CodeFragmentSerializer

    def create(self, request, *args, **kwargs):
        api_key = request.data.get("apiKey")
        logger.debug(f"Received API Key: {api_key}")
        if not api_key:
            logger.debug("API key missing.")
            return Response(
                {"status": "API key missing."}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            profile = ChatSnipProfile.objects.get(api_key=api_key)
        except ChatSnipProfile.DoesNotExist:
            logger.debug("Invalid API key.")
            return Response(
                {"status": "Invalid API key."}, status=status.HTTP_403_FORBIDDEN
            )

        data = request.data
        logger.debug(f"Received data: {data}")
        chat = Chat.objects.get(id=data.get("chat_id"))
        if check_duplicate_code_fragment(
            chat, data.get("source_code"), data.get("filename")
        ):
            logger.debug("Duplicate code fragment content.")
            return Response(
                {"status": "Duplicate content."}, status=status.HTTP_400_BAD_REQUEST
            )
        code_fragment = save_code_fragment(
            chat,
            data.get("filename"),
            data.get("source_code"),
            data.get("programming_language"),
        )
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
        context["pygments_css"] = pygments_css
        return context


class ChatCreateView(LoginRequiredMixin, CreateView):
    """View to create a new chat."""

    model = Chat
    template_name = "chatsnip/chat_form.html"
    fields = ["name", "content", "tags"]
    success_url = reverse_lazy("chatsnip:chat_list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        if check_duplicate_chat_content(
            form.instance.unique_identifier, form.instance.content
        ):
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
        if check_duplicate_code_fragment(
            form.instance.chat, form.instance.filename, form.instance.source_code
        ):
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

@login_required
def delete_fragment(request):
    fragment_id = request.POST.get("fragment_id")
    if not fragment_id:
        return JsonResponse({"status": False, "message": "No fragment ID provided."})
    code_fragment = get_object_or_404(CodeFragment, pk=fragment_id)
    code_fragment.delete()
    return JsonResponse({"status": True, "message": "Code fragment deleted."})