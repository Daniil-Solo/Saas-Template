from enum import StrEnum


class TaskName(StrEnum):
    """Имена фоновых задач; совпадают с именами функций-задач воркера."""

    SEND_EMAIL = "send_email"
    SEND_INVITATION_EMAIL = "send_invitation_email"
