# ChatSnipServer

![ChatSnipServer](chat_snip_server.webp)

## Overview

ChatSnipServer is a Django backend solution for receiving and managing chat posts from the ChatSnip Chrome extension. It allows users to save chat content with unique identifiers, manage code fragments, and avoid duplicate content using checksums.

## Features

- Save chat content with unique identifiers
- Manage code fragments associated with chats
- Avoid saving duplicate content using checksums
- Comprehensive admin interface
- API endpoints for posting content
- Styled using Bootstrap 5.3.3 and FontAwesome
- Unit tests using pytest

## Requirements

- Python 3.12 or newer
- Django 5.0 or newer

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/weholt/chatsnipserver.git
    ```
2. Navigate to the project directory:
    ```bash
    cd chatsnipserver
    ```
3. Install dependencies:
    ```bash
    pip install -e .[dev] --upgrade
    ```
4. Apply migrations:
    ```bash
    python manage.py migrate
    ```
5. Create a superuser:
    ```bash
    python manage.py createsuperuser
    ```
6. Run the development server:
    ```bash
    python manage.py runserver
    ```

## Usage

### Admin Interface

Access the admin interface at `/admin` to manage chats and code fragments.

### API Endpoints

#### Post Chat Content

- **URL:** `/api/chats/`
- **Method:** `POST`
- **Payload:**
    ```json
    {
        "unique_identifier": "unique-chat-id",
        "name": "Chat Name",
        "content": "Chat content goes here."
    }
    ```

#### Post Code Fragment

- **URL:** `/api/codefragments/`
- **Method:** `POST`
- **Payload:**
    ```json
    {
        "chat_id": "chat_id",
        "filename": "example.py",
        "programming_language": "python",
        "source_code": "print('Hello, world!')"
    }
    ```

### Chrome Extension

Download and install the ChatSnip Chrome extension to easily save and manage your chats and code fragments.

#### Installation Instructions

1. Download the extension file from [here](path_to_chrome_extension.crx).
2. Open Chrome and navigate to `chrome://extensions`.
3. Enable "Developer mode" by toggling the switch in the top right corner.
4. Drag and drop the downloaded extension file into the Chrome extensions page.

## Installed Apps

Add the following to your `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    ...
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'taggit',
    'crispy_forms',
    'crispy_bootstrap5',
    'chatsnipserver',
]
```

## License

This project is licensed under the GNU AFFERO GENERAL PUBLIC LICENSE Version 3.

## Testing

```bash

    $ python .\testsite\manage.py test

```

## Credits

- [Django](https://www.djangoproject.com/) - The web framework used.
- [Bootstrap](https://getbootstrap.com/) - For responsive design.
- [FontAwesome](https://fontawesome.com/) - For icons.
