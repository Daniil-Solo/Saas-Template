from abc import ABC, abstractmethod

from pydantic import BaseModel

from src.constants.emails import EmailTemplate
from src.dto.emails import RenderedEmail


class EmailTemplater(ABC):
    @abstractmethod
    def render(self, template: EmailTemplate, context: BaseModel) -> RenderedEmail:
        """Рендерит тему, HTML и текст письма; пропущенная переменная шаблона - ошибка."""
        raise NotImplementedError
