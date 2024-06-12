from django.contrib import admin
from django.utils.html import mark_safe

from .models import Chat, ChatImage, ChatSnipProfile, CodeFragment


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


def blacklist_images(modeladmin, request, queryset):
    queryset.update(blacklisted=True)


blacklist_images.short_description = "Blacklists selected images"


@admin.register(ChatImage)
class ChatImageAdmin(admin.ModelAdmin):
    list_display = ("title", "image_tag", "checksum", "blacklisted")
    list_filter = ("blacklisted",)
    actions = [blacklist_images]

    def image_tag(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="150" height="150" />')
        return "No Image"

    image_tag.short_description = "Image"
