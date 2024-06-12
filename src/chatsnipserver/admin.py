from django.contrib import admin

from .models import Chat, ChatSnipProfile, CodeFragment


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ("name", "unique_identifier", "user", "timestamp", "checksum")
    search_fields = ("name", "unique_identifier", "user__username", "content")
    list_filter = ("timestamp", "tags", "user")
    readonly_fields = ("checksum", "timestamp")


@admin.register(CodeFragment)
class CodeFragmentAdmin(admin.ModelAdmin):
    list_display = ("filename", "programming_language", "chat", "timestamp", "checksum", "selected")
    search_fields = ("filename", "programming_language", "chat__name", "source_code")
    list_filter = ("timestamp", "programming_language", "chat", "selected")
    readonly_fields = ("checksum", "timestamp")


@admin.register(ChatSnipProfile)
class ChatSnipProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "api_key")
    search_fields = ("user__username", "api_key")
