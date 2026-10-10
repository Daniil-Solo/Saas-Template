"""Предпросмотр писем: `python -m src.interfaces.cli.email_preview [--template welcome] [--out .preview]`."""

import argparse
import datetime
from pathlib import Path

from pydantic import BaseModel

from src.constants.emails import EmailTemplate
from src.dto.emails import InvitationEmailContext, WelcomeEmailContext
from src.infrastructure.email_templater.jinja2 import Jinja2EmailTemplater
from src.settings import get_settings

# Образец контекста для каждого письма; без записи падает тест на все шаблоны
SAMPLE_CONTEXTS: dict[EmailTemplate, BaseModel] = {
    EmailTemplate.WELCOME: WelcomeEmailContext(
        fullname="Анна Иванова",
        login_url="http://localhost:5173/login",
    ),
    EmailTemplate.INVITATION: InvitationEmailContext(
        invited_by_name="Пётр Петров",
        organization_name="Ромашка",
        role_names=["Менеджер", "Аналитик"],
        expires_at=datetime.datetime(2030, 1, 8, 12, 0, tzinfo=datetime.UTC),
        accept_url="http://localhost:5173/invitations/sample-token",
    ),
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Рендерит письма с образцами данных в HTML и текст")
    parser.add_argument("--template", choices=[template.value for template in EmailTemplate], default=None)
    parser.add_argument("--out", default=".preview", help="Папка для результата")
    args = parser.parse_args()

    settings = get_settings()
    templater = Jinja2EmailTemplater(settings.app, settings.email)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    templates = [EmailTemplate(args.template)] if args.template else list(EmailTemplate)
    for template in templates:
        rendered = templater.render(template, SAMPLE_CONTEXTS[template])
        (out / f"{template.value}.html").write_text(rendered.html, encoding="utf-8")
        (out / f"{template.value}.txt").write_text(f"Тема: {rendered.subject}\n\n{rendered.text}", encoding="utf-8")
        print(f"{template.value}: {out / f'{template.value}.html'}")  # noqa: T201


if __name__ == "__main__":
    main()
