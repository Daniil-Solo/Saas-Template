import pytest

from src.constants.emails import EmailTemplate
from src.dto.emails import EMAIL_CONTEXTS
from src.interfaces.cli.email_preview import SAMPLE_CONTEXTS


@pytest.mark.parametrize("template", list(EmailTemplate))
def test__template_has_context_and_sample(template):
    assert template in EMAIL_CONTEXTS
    assert isinstance(SAMPLE_CONTEXTS[template], EMAIL_CONTEXTS[template])
