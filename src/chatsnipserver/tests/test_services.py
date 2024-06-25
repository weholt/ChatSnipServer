import hashlib
import os

import django
import pytest
from chatsnipserver.services import (
    clean_content,
    generate_checksum,
    has_duplicate_checksum,
    parse_source_code_fragments,
)
from django.conf import settings
from django.contrib.auth import get_user_model

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "testsite.settings")
django.setup()

from chatsnipserver.models import Chat, CodeFragment
from chatsnipserver.services import (
    check_duplicate_chat_content,
    check_duplicate_code_fragment,
    clean_content,
    generate_checksum,
    identify_language,
)


@pytest.mark.parametrize(
    "content,expected_checksum",
    [
        (
            "Hello, world!",
            "64ec88ca00b268e5ba1a35678a1b5316d212f4f366b2477240e1f4b4ed7e87f5",
        ),
        (
            "   Hello,  world!  ",
            "64ec88ca00b268e5ba1a35678a1b5316d212f4f366b2477240e1f4b4ed7e87f5",
        ),
    ],
)
def test_generate_checksum_2(content, expected_checksum):
    assert generate_checksum(content) == expected_checksum


def test_identify_language():
    content = "print('Hello, world!')"
    assert identify_language(content) == "python"


@pytest.mark.django_db
def test_clean_content_2():
    user = get_user_model().objects.create(username="testuser", password="testpass")
    chat = Chat.objects.create(
        unique_identifier="123",
        name="Test Chat",
        content="This is a test chat.",
        user=user,
    )
    filename = "example.py"
    programming_language = "python"
    content = "print('Hello, world!')"
    assert clean_content(chat, filename, programming_language, content) == content


@pytest.mark.django_db
def test_check_duplicate_chat_content():
    user = get_user_model().objects.create(username="testuser", password="testpass")
    chat = Chat.objects.create(
        unique_identifier="123",
        name="Test Chat",
        content="This is a test chat.",
        user=user,
    )
    new_content = "This is a test chat."
    assert check_duplicate_chat_content(chat, new_content) == True


@pytest.mark.django_db
def test_check_duplicate_code_fragment():
    user = get_user_model().objects.create(username="testuser", password="testpass")
    chat = Chat.objects.create(
        unique_identifier="123",
        name="Test Chat",
        content="This is a test chat.",
        user=user,
    )
    code_fragment = CodeFragment.objects.create(
        chat=chat,
        filename="test.py",
        programming_language="python",
        source_code='print("Hello, world!")',
    )
    new_content = 'print("Hello, world!")'
    assert check_duplicate_code_fragment(chat, "test.py", new_content) == True


@pytest.fixture
def content():
    return """
    # filename: example1.py
    print("Hello, World!")
    # endof
    
    Copy code
    # filename: example2.py
    def hello():
        print("Hello, World!")
    # endof
    
    ```
    # filename: example3.py
    print("Hello again!")
    ```
    
    ```python
    # filename: example4.py
    def greet():
        print("Greetings!")
    ```
    """


@pytest.fixture
def existing_fragments_2():
    return [
        ("example1.py", 'print("Hello, World!")'),
        ("example2.py", 'def hello():\n    print("Hello, World!")'),
    ]


def test_parse_source_code_fragments_2(content):
    expected_fragments = [
        ("example1.py", 'print("Hello, World!")'),
        ("example2.py", 'def hello():\n    print("Hello, World!")'),
        ("example3.py", 'print("Hello again!")'),
        ("example4.py", 'def greet():\n    print("Greetings!")'),
    ]
    parsed_fragments = parse_source_code_fragments(content)
    assert parsed_fragments == expected_fragments


def test_generate_checksum_2():
    code = 'print("Hello, World!")'
    normalized_content = "".join(code.split())
    expected_checksum = hashlib.sha256(normalized_content.encode("utf-8")).hexdigest()
    assert generate_checksum(code) == expected_checksum


def test_has_duplicate_checksum_2(existing_fragments):
    new_fragment = ("example1.py", 'print("Hello, World!")')
    assert has_duplicate_checksum(existing_fragments, new_fragment) == True

    new_fragment = ("example5.py", 'print("New code!")')
    assert has_duplicate_checksum(existing_fragments, new_fragment) == False


@pytest.fixture
def content():
    return """
    # filename: example1.py
    print("Hello, World!")
    # endof
    
    Copy code
    # filename: example2.py
    def hello():
        print("Hello, World!")
    # endof
    
    ```
    # filename: example3.py
    print("Hello again!")
    ```
    
    ```python
    # filename: example4.py
    def greet():
        print("Greetings!")
    ```
    """


@pytest.fixture
def existing_fragments():
    return [
        ("example1.py", 'print("Hello, World!")'),
        ("example2.py", 'def hello():\n    print("Hello, World!")'),
    ]


def test_parse_source_code_fragments(content):
    expected_fragments = [
        ("example1.py", 'print("Hello, World!")'),
        ("example2.py", 'def hello():\n    print("Hello, World!")'),
        ("example3.py", 'print("Hello again!")'),
        ("example4.py", 'def greet():\n    print("Greetings!")'),
    ]
    parsed_fragments = parse_source_code_fragments(content)
    assert parsed_fragments == expected_fragments


def test_generate_checksum():
    code = 'print("Hello, World!")'
    expected_checksum = hashlib.md5(code.encode("utf-8")).hexdigest()
    assert generate_checksum(code) == expected_checksum


def test_has_duplicate_checksum(existing_fragments):
    new_fragment = ("example1.py", 'print("Hello, World!")')
    assert has_duplicate_checksum(existing_fragments, new_fragment) == True

    new_fragment = ("example5.py", 'print("New code!")')
    assert has_duplicate_checksum(existing_fragments, new_fragment) == False


@pytest.mark.django_db
def test_clean_content():
    raw_code = """
    # filename: test.py
    ```
    print("This is a test.")
    ```
    # endof
    """
    user = get_user_model().objects.create(username="testuser", password="testpass")
    expected_cleaned_code = 'print("This is a test.")'
    chat = Chat.objects.create(
        unique_identifier="123",
        name="Test Chat",
        content="This is a test chat.",
        user=user,
    )
    cleaned_code = clean_content(raw_code, chat)
    assert cleaned_code == expected_cleaned_code
