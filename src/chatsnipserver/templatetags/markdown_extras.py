import markdown
from django import template
from django.utils.safestring import mark_safe
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

register = template.Library()

@register.filter(name='highlight')
def highlight_code(code, language):
    """
    Syntax highlight the code using Pygments.
    :param code: The code to highlight
    :param language: The programming language of the code
    :return: Syntax-highlighted HTML
    """
    try:
        lexer = get_lexer_by_name(language)
    except:
        lexer = get_lexer_by_name('text')
    formatter = HtmlFormatter()
    highlighted_code = highlight(code, lexer, formatter)
    return mark_safe(highlighted_code)

@register.filter(name='markdown')
def markdown_format(text):
    return mark_safe(markdown.markdown(text, extensions=['codehilite', "fenced_code"]))