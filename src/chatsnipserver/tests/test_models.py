import pytest
from django.contrib.auth import get_user_model

from chatsnipserver.models import Chat, CodeFragment
from chatsnipserver.services import generate_checksum


@pytest.mark.django_db
def test_chat_creation():
    user = get_user_model().objects.create(username="testuser", password="testpass")
    chat = Chat.objects.create(unique_identifier="123", name="Test Chat", content="This is a test chat.", user=user)
    assert chat.unique_identifier == "123"
    assert chat.name == "Test Chat"
    assert chat.content == "This is a test chat."
    assert chat.user == user
    assert chat.checksum == generate_checksum("This is a test chat.")


@pytest.mark.django_db
def test_code_fragment_creation():
    user = get_user_model().objects.create(username="testuser", password="testpass")
    chat = Chat.objects.create(unique_identifier="123", name="Test Chat", content="This is a test chat.", user=user)
    code_fragment = CodeFragment.objects.create(chat=chat, filename="test.py", programming_language="python", source_code='print("Hello, world!")')
    assert code_fragment.chat == chat
    assert code_fragment.filename == "test.py"
    assert code_fragment.programming_language == "python"
    assert code_fragment.source_code == 'print("Hello, world!")'
    assert code_fragment.checksum == generate_checksum('print("Hello, world!")')
