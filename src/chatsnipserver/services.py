import hashlib
import os
import re
import uuid
from datetime import datetime
from io import BytesIO
from typing import IO, List, Tuple

import requests
from django.core.files.base import ContentFile

from .models import Chat, ChatImage, CodeFragment


def parse_source_code_fragments(content: str) -> List[Tuple[str, str]]:
    """Parses the content to extract source code fragments based on different detection methods.

    This function looks for code fragments based on various heuristics:
    1. Template described in the instructions.
    2. 'Copy code' markers.
    3. Triple backticks for code blocks.
    4. Markdown fenced code blocks.

    Args:
        content (str): The chat content to parse.

    Returns:
        List[Tuple[str, str]]: A list of tuples where each tuple contains the filename and the code fragment.
    """
    fragments = []

    # Method 1: Template described in the instructions
    template_pattern = re.compile(r"# filename: (.+?)\n(.*?)\n# endof", re.DOTALL)
    fragments.extend(re.findall(template_pattern, content))

    # Method 2: 'Copy code' markers
    copy_code_pattern = re.compile(r"Copy code\n# filename: (.+?)\n(.*?)\n# endof", re.DOTALL)
    fragments.extend(re.findall(copy_code_pattern, content))

    # Method 3: Triple backticks for code blocks
    triple_backticks_pattern = re.compile(r"```(?:\w*\n)?(.*?)```", re.DOTALL)
    code_blocks = re.findall(triple_backticks_pattern, content)
    for block in code_blocks:
        filename_match = re.match(r"# filename: (.+?)\n", block)
        if filename_match:
            filename = filename_match.group(1).strip()
            code = block[len(filename_match.group(0)) :].strip()
            fragments.append((filename, code))
        else:
            fragments.append((None, block.strip()))

    # Method 4: Markdown fenced code blocks
    markdown_fenced_pattern = re.compile(r"```[\w]*\n(.*?)```", re.DOTALL)
    fragments.extend([(None, match.strip()) for match in re.findall(markdown_fenced_pattern, content)])

    return fragments


def clean_content(code: str, chat: Chat, filename: str | None = "", programming_language: str | None = "") -> str:
    """Cleans the content of the source code by removing unnecessary lines.

    This function removes lines containing `# filename:` and `# endof`, and ensures
    that triple backticks are not the first or last lines in the source code.

    Args:
        code (str): The source code to clean.

    Returns:
        str: The cleaned source code.
    """
    lines = code.split("\n")
    cleaned_lines = [line for line in lines if not (line.startswith("# filename:") or line.startswith("# endof"))]

    # Ensure triple backticks are not the first or last lines
    if cleaned_lines[0].strip() == "```":
        cleaned_lines = cleaned_lines[1:]
    if cleaned_lines[-1].strip() == "```":
        cleaned_lines = cleaned_lines[:-1]

    return "\n".join(cleaned_lines)


def has_duplicate_checksum(existing_fragments: List[Tuple[str, str]], new_fragment: Tuple[str, str]) -> bool:
    """Checks if a new fragment has a duplicate checksum in the existing fragments.

    Args:
        existing_fragments (List[Tuple[str, str]]): The list of existing source code fragments.
        new_fragment (Tuple[str, str]): The new source code fragment to check.

    Returns:
        bool: True if a duplicate checksum is found, False otherwise.
    """
    new_checksum = generate_checksum(new_fragment[1])
    for filename, code in existing_fragments:
        if filename == new_fragment[0] and generate_checksum(code) == new_checksum:
            return True
    return False


def generate_checksum(content: str) -> str:
    """
    Generate a SHA-256 checksum for the given content.

    Args:
        content (str): The content to generate the checksum for.

    Returns:
        str: The generated checksum.
    """
    normalized_content = "".join(content.split())
    return hashlib.sha256(normalized_content.encode("utf-8")).hexdigest()


def identify_language(content: str) -> str:
    """
    Identify the programming language of the given content.

    Args:
        content (str): The content to identify the language for.

    Returns:
        str: The identified programming language.
    """
    # Placeholder for language identification logic
    return "python"


def get_or_create_chat(identifier: str, name: str, user) -> Chat:
    """
    Get or create a chat with the given identifier.

    Args:
        identifier (str): The unique identifier of the chat.
        name (str): The name of the chat.
        user (User): The user associated with the chat.

    Returns:
        Chat: The retrieved or newly created chat.
    """
    chat, created = Chat.objects.get_or_create(unique_identifier=identifier, defaults={"name": name, "user": user})
    if not created:
        chat.name = name
        chat.save()
    return chat


def save_code_fragment(chat: Chat, filename: str, content: str, language: str = "") -> CodeFragment | None:
    """
    Save a code fragment associated with a chat.

    Args:
        chat (Chat): The chat object.
        filename (str): The filename of the code fragment.
        content (str): The content of the code fragment.
        language (str, optional): The programming language of the code fragment. Defaults to None.

    Returns:
        CodeFragment: The saved code fragment.
    """
    if check_duplicate_code_fragment(chat, filename, content):
        return

    if not language:
        language = identify_language(content)
    code_fragment = CodeFragment(chat=chat, filename=filename, programming_language=language, source_code=content)
    code_fragment.save()
    return code_fragment


def compose_chat_view(chat: Chat) -> dict:
    """
    Compose a view of the chat including the selected code fragments.

    Args:
        chat (Chat): The chat object.

    Returns:
        dict: The context for the chat view including selected code fragments.
    """
    fragments = chat.code_fragments.all()
    grouped_fragments = {}
    for fragment in fragments:
        if fragment.filename not in grouped_fragments:
            grouped_fragments[fragment.filename] = []
        grouped_fragments[fragment.filename].append(fragment)

    selected_fragments = {filename: max(group, key=lambda x: x.selected or x.timestamp) for filename, group in grouped_fragments.items()}
    return {"chat": chat, "selected_fragments": selected_fragments}


def compose_source_code_view(chat: Chat) -> dict:
    """
    Compose a view of the source code with tabs for different versions.

    Args:
        chat (Chat): The chat object.

    Returns:
        dict: The context for the source code view including grouped code fragments.
    """
    fragments = chat.code_fragments.all()
    grouped_fragments = {}
    for fragment in fragments:
        if fragment.filename not in grouped_fragments:
            grouped_fragments[fragment.filename] = []
        grouped_fragments[fragment.filename].append(fragment)
    return {"chat": chat, "grouped_fragments": grouped_fragments}


def check_duplicate_chat_content(chat: Chat, new_content: str) -> bool:
    """
    Check if the new content is a duplicate of the existing chat content.

    Args:
        identifier (str): The unique identifier of the chat.
        new_content (str): The new content to check.

    Returns:
        bool: True if the content is a duplicate, False otherwise.
    """
    new_checksum = generate_checksum(new_content)
    return chat.checksum == new_checksum


def check_duplicate_code_fragment(chat: Chat, filename: str, new_content: str) -> bool:
    """
    Check if the new content is a duplicate of an existing code fragment within the chat.

    Args:
        chat (Chat): The chat object.
        filename (str): The filename of the code fragment.
        new_content (str): The new content to check.

    Returns:
        bool: True if the content is a duplicate, False otherwise.
    """
    new_checksum = generate_checksum(new_content)
    existing_fragments = chat.code_fragments.filter(filename=filename)
    for fragment in existing_fragments:
        if fragment.checksum == new_checksum:
            return True
    return False


def get_pretty_date() -> str:
    """Returns the current date and time in a human-readable, pretty format.

    The format will be:
    - Weekday name (e.g., Monday)
    - Month name (e.g., January)
    - Day of the month (e.g., 01, 23)
    - Year (e.g., 2024)
    - 12-hour clock time (e.g., 08:30 PM)

    Returns:
        str: The current date and time as a formatted string.
    """
    now = datetime.now()
    return now.strftime("%A, %B %d, %Y %I:%M %p")


def get_unique_filename(filename, file_extension=None):
    """Generate a unique filename by appending a UUID."""
    if not file_extension:
        _, file_extension = os.path.splitext(filename)
    unique_name = f"{uuid.uuid4().hex}{file_extension}"
    return unique_name


def detect_image_type(file: IO) -> str | None:
    header = file.read(16)
    if header.startswith(b"\xff\xd8"):
        return ".jpg"
    elif header.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    elif header.startswith(b"GIF87a") or header.startswith(b"GIF89a"):
        return ".gif"
    elif header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return ".webp"
    elif header[:4] == b"\x00\x00\x00\x00" and header[4:8] == b"ftyp":
        if header[8:12] in [b"avif"]:
            return ".avif"


def download_and_save_image(chat, image_url, title=None, description=None) -> dict:
    if ChatImage.objects.filter(chat=chat, source_url=image_url).exists():
        return {"status": "Image already exists"}

    if ChatImage.objects.filter(source_url=image_url, blacklisted=True).exists():
        return {"status": "Image is blacklisted"}

    response = requests.get(image_url)
    if response.status_code == 200:
        checksum = ChatImage.checksum_from_content(response.content)
        if ChatImage.exists_with_checksum(chat, checksum):
            return {"status": "Image with same checksum already exists"}

        image_name = os.path.basename(image_url)
        file_extension = detect_image_type(BytesIO(response.content))
        unique_image_name = get_unique_filename(image_name, file_extension)

        chat_image = ChatImage(chat=chat, source_url=image_url, title=title, description=description)

        chat_image.image.save(unique_image_name, ContentFile(response.content), save=True)
        return {"status": "Image downloaded", "image": chat_image}
    else:
        return {"status": "Failed to download image", "Status code": f"{response.status_code}"}
