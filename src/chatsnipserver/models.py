import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from taggit.managers import TaggableManager

User = get_user_model()


class Chat(models.Model):
    """Model representing a chat."""

    unique_identifier = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now=True)
    tags = TaggableManager()
    content = models.TextField()
    checksum = models.CharField(max_length=64)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="chats")

    class Meta:
        verbose_name = "Chat"
        verbose_name_plural = "Chats"
        ordering = ["-timestamp"]

    def save(self, *args, **kwargs):
        """Generate checksum and save the chat."""
        from .services import generate_checksum

        self.checksum = generate_checksum(self.content)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class CodeFragment(models.Model):
    """Model representing a code fragment within a chat."""

    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="code_fragments")
    filename = models.CharField(max_length=255, null=True, blank=True)
    programming_language = models.CharField(max_length=50, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    source_code = models.TextField()
    checksum = models.CharField(max_length=64)
    selected = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Code Fragment"
        verbose_name_plural = "Code Fragments"
        ordering = ["-timestamp"]

    def save(self, *args, **kwargs):
        """Clean content, generate checksum and save the code fragment."""
        from .services import clean_content, generate_checksum

        self.source_code = clean_content(self.source_code, self.chat, self.filename, self.programming_language)
        self.checksum = generate_checksum(self.source_code)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.filename or 'No Filename'} - {self.programming_language or 'Unknown Language'}"


class ChatSnipProfile(models.Model):
    """Model representing a user profile with API key."""

    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    api_key = models.CharField(max_length=255, unique=True, default=uuid.uuid4)

    def regenerate_api_key(self):
        """Regenerate the API key for the user."""
        self.api_key = uuid.uuid4()
        self.save()
