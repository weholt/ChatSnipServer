from django import forms

from .models import ChatSnipProfile, Chat
from aceshigh.widgets import AceEditorWidget


class ChatSnipProfileForm(forms.ModelForm):
    class Meta:
        model = ChatSnipProfile
        fields = ["api_key"]
        widgets = {
            "api_key": forms.TextInput(attrs={"readonly": "readonly"}),
        }

class ChatForm(forms.ModelForm):
    class Meta:
        model = Chat
        fields = ['name', 'tags', 'json_data', 'markdown']
        widgets = {
            'json_data': AceEditorWidget(mode='json'),
            'markdown': AceEditorWidget(mode='markdown'),
        }