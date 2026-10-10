class EmailSendError(Exception):
    """Ошибка отправки письма. В сообщении нет адреса получателя и содержимого письма."""


class EmailTemporaryError(EmailSendError):
    """Временный сбой (сеть, таймаут, 429/5xx): отправку стоит повторить."""


class EmailPermanentError(EmailSendError):
    """Постоянная ошибка (неверный адрес, отказ в доступе): повтор не поможет."""
