from django import forms

from .models import ChatSnipProfile


class ChatSnipProfileForm(forms.ModelForm):
    class Meta:
        model = ChatSnipProfile
        fields = ["api_key"]
        widgets = {
            "api_key": forms.TextInput(attrs={"readonly": "readonly"}),
        }
