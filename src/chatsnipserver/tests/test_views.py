import pytest
from chatsnipserver.models import Chat, CodeFragment
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_chat_create_view():
    user = get_user_model().objects.create_user(
        username="testuser", password="testpass"
    )
    client = APIClient()
    client.force_authenticate(user=user)

    url = reverse("chatsnip:chat_list")
    data = {
        "unique_identifier": "123",
        "name": "Test Chat",
        "content": "This is a test chat.",
    }
    response = client.post(url, data, format="json")

    # Debugging: print response status code and content
    print(user.is_authenticated)
    print(response.status_code)
    print(response.content)

    # Ensure the response is successful
    assert (
        response.status_code == 201
    )  # Assuming the view returns a 201 status code for a successful creation

    # Check the response data
    assert response.data["status"] == "Chat saved."


@pytest.mark.django_db
def test_code_fragment_create_view():
    user = get_user_model().objects.create(username="testuser", password="testpass")
    client = APIClient()
    client.force_authenticate(user=user)
    chat = Chat.objects.create(
        unique_identifier="123",
        name="Test Chat",
        content="This is a test chat.",
        user=user,
    )
    url = reverse("chatsnip:codefragment_list")

    data = {
        "chat_id": chat.id,
        "filename": "test.py",
        "programming_language": "python",
        "source_code": 'print("Hello, world!")',
    }
    response = client.post(url, data, format="json")
    assert response.status_code == 201
    assert response.data["status"] == "Code fragment saved."
