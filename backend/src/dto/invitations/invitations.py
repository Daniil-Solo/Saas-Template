import datetime

from pydantic import Field

from src.constants.invitations import InvitationDisplayStatus, InvitationStatus
from src.dto.common import BaseDTO, NormalizedEmail
from src.dto.roles import RoleDTO


class InvitationCreateDTO(BaseDTO):
    email: NormalizedEmail = Field(description="Email приглашаемого (в нижнем регистре)")
    role_ids: list[int] = Field(default_factory=list, description="ID ролей, которые получит приглашённый")


class InvitationRecordDTO(BaseDTO):
    """Строка приглашения из БД: внутренний DTO, наружу не отдаётся."""

    id: int
    organization_id: int
    email: str
    status: InvitationStatus
    expires_at: datetime.datetime
    invited_by_id: int | None
    created_at: datetime.datetime
    accepted_at: datetime.datetime | None


class InvitationDTO(BaseDTO):
    id: int = Field(description="ID приглашения")
    organization_id: int = Field(description="ID организации")
    email: str = Field(description="Email приглашаемого")
    status: InvitationDisplayStatus = Field(description="Статус: active, accepted, revoked, expired")
    roles: list[RoleDTO] = Field(description="Роли, которые получит приглашённый (удалённые роли не показываются)")
    expires_at: datetime.datetime = Field(description="Срок действия")
    invited_by_id: int | None = Field(description="ID пригласившего (null, если пользователь удалён)")
    created_at: datetime.datetime = Field(description="Дата создания")
    accepted_at: datetime.datetime | None = Field(description="Дата принятия")


class InvitationCreatedDTO(InvitationDTO):
    token: str = Field(description="Токен приглашения для ссылки; показывается только один раз")


class InvitationPreviewDTO(BaseDTO):
    organization_id: int = Field(description="ID организации")
    organization_name: str = Field(description="Название организации")
    email: str = Field(description="Email, на который выдано приглашение")
    status: InvitationDisplayStatus = Field(description="Статус: active, accepted, revoked, expired")
    roles: list[RoleDTO] = Field(description="Роли, которые получит приглашённый")
    expires_at: datetime.datetime = Field(description="Срок действия")
