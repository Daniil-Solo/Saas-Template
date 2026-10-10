from pydantic import BaseModel

from src.constants.emails import EmailTemplate
from src.dto.emails.emails import (
    EmailContextDTO,
    EmailEnqueuedDTO,
    EmailMessage,
    EmailSendRequestDTO,
    EmailTemplateInfoDTO,
    InvitationEmailContext,
    RenderedEmail,
    WelcomeEmailContext,
)

# Единственное место, связывающее тип письма с DTO его контекста
EMAIL_CONTEXTS: dict[EmailTemplate, type[BaseModel]] = {
    EmailTemplate.WELCOME: WelcomeEmailContext,
    EmailTemplate.INVITATION: InvitationEmailContext,
}

__all__ = [
    "EMAIL_CONTEXTS",
    "EmailContextDTO",
    "EmailEnqueuedDTO",
    "EmailMessage",
    "EmailSendRequestDTO",
    "EmailTemplateInfoDTO",
    "InvitationEmailContext",
    "RenderedEmail",
    "WelcomeEmailContext",
]
