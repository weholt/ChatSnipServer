from rest_framework import serializers

from .models import Chat, CodeFragment


class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = ["unique_identifier", "name", "content"]


class CodeFragmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeFragment
        fields = ["chat", "filename", "programming_language", "source_code"]
