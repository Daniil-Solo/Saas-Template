import pytest

from src.constants.emails import EmailTemplate
from src.dto.emails import WelcomeEmailContext
from src.infrastructure.email_templater.jinja2 import Jinja2EmailTemplater
from src.interfaces.cli.email_preview import SAMPLE_CONTEXTS
from src.settings import AppSettings, EmailSettings


@pytest.fixture
def templater():
    return Jinja2EmailTemplater(AppSettings(), EmailSettings(from_display_name="Сервис"))


@pytest.mark.parametrize("template", list(EmailTemplate))
def test__renders_every_template(templater, template):
    rendered = templater.render(template, SAMPLE_CONTEXTS[template])

    assert rendered.subject.strip() and "\n" not in rendered.subject
    assert rendered.html.lstrip().startswith("<!doctype html>")
    assert 'lang="ru"' in rendered.html
    assert "prefers-color-scheme: dark" in rendered.html
    assert rendered.text.strip()


@pytest.mark.parametrize("template", list(EmailTemplate))
def test__link_is_in_button_duplicate_and_text(templater, template):
    context = SAMPLE_CONTEXTS[template]
    url = getattr(context, "login_url", None) or context.accept_url

    rendered = templater.render(template, context)

    assert rendered.html.count(url) >= 3  # href кнопки, href дубля и текст дубля
    assert url in rendered.text


def test__html_escapes_user_values(templater):
    context = WelcomeEmailContext(fullname="<script>alert(1)</script>", login_url="http://x/login")

    rendered = templater.render(EmailTemplate.WELCOME, context)

    assert "<script>alert(1)</script>" not in rendered.html
    assert "&lt;script&gt;" in rendered.html


def test__subject_has_no_newlines(templater):
    context = WelcomeEmailContext(fullname="Имя\nс переносом", login_url="http://x/login")

    assert "\n" not in templater.render(EmailTemplate.WELCOME, context).subject


def test__strict_undefined_fails(templater):
    class Incomplete:
        def model_dump(self):
            return {"fullname": "Анна"}

    with pytest.raises(Exception, match="login_url"):
        templater.render(EmailTemplate.WELCOME, Incomplete())
