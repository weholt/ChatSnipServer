from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "chatsnip"

router = DefaultRouter()
router.register(r"chats", views.ChatViewSet, basename="chat")
router.register(r"codefragments", views.CodeFragmentViewSet, basename="codefragment")

urlpatterns = [
    path("api/", include(router.urls)),
    path("chat/", views.ChatListView.as_view(), name="chat_list"),
    path("chat/create/", views.ChatCreateView.as_view(), name="chat_create"),
    path("chat/<int:pk>/", views.ChatDetailView.as_view(), name="chat_detail"),
    path("chat/<int:pk>/update/", views.ChatUpdateView.as_view(), name="chat_update"),
    path("chat/<int:pk>/delete/", views.ChatDeleteView.as_view(), name="chat_delete"),
    path("codefragment/", views.CodeFragmentListView.as_view(), name="codefragment_list"),
    path("codefragment/create/", views.CodeFragmentCreateView.as_view(), name="codefragment_create"),
    path("codefragment/<int:pk>/", views.CodeFragmentDetailView.as_view(), name="codefragment_detail"),
    path("codefragment/<int:pk>/update/", views.CodeFragmentUpdateView.as_view(), name="codefragment_update"),
    path("codefragment/<int:pk>/delete/", views.CodeFragmentDeleteView.as_view(), name="codefragment_delete"),
    path("extension/", views.ExtensionDetailView.as_view(), name="extension_detail"),
    path("profile/", views.ChatSnipProfileUpdateView.as_view(), name="profile"),
    path("profile/regenerate-api-key/", views.regenerate_api_key, name="regenerate_api_key"),
]
