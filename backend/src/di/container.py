from dependency_injector import containers, providers

from src.infrastructure.dao.invitations.sqlalchemy import SQLAlchemyInvitationsDAO
from src.infrastructure.dao.members.sqlalchemy import SQLAlchemyMembersDAO
from src.infrastructure.dao.organizations.sqlalchemy import SQLAlchemyOrganizationsDAO
from src.infrastructure.dao.roles.sqlalchemy import SQLAlchemyRolesDAO
from src.infrastructure.dao.users.sqlalchemy import SQLAlchemyUsersDAO
from src.infrastructure.sqlalchemy.engine import create_session_factory, init_engine
from src.infrastructure.sqlalchemy.uow import UnitOfWork
from src.settings import AdminSettings, AuthSettings, DBSettings, InvitationSettings


class Container(containers.DeclarativeContainer):
    auth_settings = providers.Singleton(AuthSettings)
    db_settings = providers.Singleton(DBSettings)
    invitation_settings = providers.Singleton(InvitationSettings)
    admin_settings = providers.Singleton(AdminSettings)

    engine = providers.Resource(init_engine, settings=db_settings)
    session_factory = providers.Singleton(create_session_factory, engine=engine)

    users_dao = providers.Factory(lambda: SQLAlchemyUsersDAO)
    organizations_dao = providers.Factory(lambda: SQLAlchemyOrganizationsDAO)
    members_dao = providers.Factory(lambda: SQLAlchemyMembersDAO)
    roles_dao = providers.Factory(lambda: SQLAlchemyRolesDAO)
    invitations_dao = providers.Factory(lambda: SQLAlchemyInvitationsDAO)

    uow = providers.Factory(
        UnitOfWork,
        session_factory=session_factory,
        users_dao_factory=users_dao,
        organizations_dao_factory=organizations_dao,
        members_dao_factory=members_dao,
        roles_dao_factory=roles_dao,
        invitations_dao_factory=invitations_dao,
    )


async def init_container() -> Container:
    container = Container()
    container.wire(
        packages=[
            "src.application.auth",
            "src.application.organizations",
            "src.application.roles",
            "src.application.invitations",
        ]
    )
    await container.init_resources()  # type: ignore[misc]
    return container


async def shutdown_container(container: Container) -> None:
    await container.shutdown_resources()  # type: ignore[misc]
    container.unwire()
