import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.exceptions import OrganizationNotFoundError
from src.dto.organizations import OrganizationDTO
from src.infrastructure.dao.organizations.interface import OrganizationsDAO
from src.infrastructure.sqlalchemy.models import organization_members_table, organizations_table


class SQLAlchemyOrganizationsDAO(OrganizationsDAO):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, name: str, created_by_id: int) -> OrganizationDTO:
        query = (
            sa.insert(organizations_table).values(name=name, created_by_id=created_by_id).returning(organizations_table)
        )
        result = await self.session.execute(query)
        return OrganizationDTO.model_validate(result.one())

    async def get_by_id(self, organization_id: int) -> OrganizationDTO:
        query = sa.select(organizations_table).where(organizations_table.c.id == organization_id)
        result = await self.session.execute(query)
        row = result.one_or_none()
        if row is None:
            raise OrganizationNotFoundError
        return OrganizationDTO.model_validate(row)

    async def list_for_user(self, user_id: int) -> list[OrganizationDTO]:
        query = (
            sa.select(organizations_table)
            .join(organization_members_table, organization_members_table.c.organization_id == organizations_table.c.id)
            .where(organization_members_table.c.user_id == user_id)
            .order_by(organizations_table.c.id)
        )
        result = await self.session.execute(query)
        return [OrganizationDTO.model_validate(row) for row in result.all()]
