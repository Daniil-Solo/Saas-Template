from enum import StrEnum


class EmailTemplate(StrEnum):
    """Типы писем; каждому соответствует папка в `infrastructure/email_templater/templates/`."""

    WELCOME = "welcome"
    INVITATION = "invitation"
