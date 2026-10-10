from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from pydantic import BaseModel

from src.constants.emails import EmailTemplate
from src.dto.emails import RenderedEmail
from src.infrastructure.email_templater.interface import EmailTemplater
from src.settings import AppSettings, EmailSettings

TEMPLATES_DIR = Path(__file__).parent / "templates"


class Jinja2EmailTemplater(EmailTemplater):
    def __init__(self, app_settings: AppSettings, email_settings: EmailSettings) -> None:
        self._env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            # Экранируются только HTML-шаблоны; тема и текст - обычный текст
            autoescape=select_autoescape(enabled_extensions=("html.j2",), default=False),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self._common = {
            "app_name": email_settings.from_display_name,
            "base_url": app_settings.base_url.rstrip("/"),
        }

    def render(self, template: EmailTemplate, context: BaseModel) -> RenderedEmail:
        variables = {**self._common, **context.model_dump()}
        subject = self._env.get_template(f"{template.value}/subject.txt.j2").render(variables)
        return RenderedEmail(
            # Тема - одна строка: переводы строк (в т.ч. из пользовательских значений) убираем
            subject=" ".join(subject.split()),
            html=self._env.get_template(f"{template.value}/body.html.j2").render(variables),
            text=self._env.get_template(f"{template.value}/body.txt.j2").render(variables).strip() + "\n",
        )
