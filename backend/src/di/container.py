from dependency_injector import containers, providers

from src.infrastructure.dao.users.sqlalchemy import SQLAlchemyUsersDAO
from src.infrastructure.sqlalchemy.engine import create_session_factory, init_engine
from src.infrastructure.sqlalchemy.uow import UnitOfWork
from src.settings import AuthSettings, DBSettings


class Container(containers.DeclarativeContainer):
    auth_settings = providers.Singleton(AuthSettings)
    db_settings = providers.Singleton(DBSettings)

    engine = providers.Resource(init_engine, settings=db_settings)
    session_factory = providers.Singleton(create_session_factory, engine=engine)

    users_dao = providers.Factory(lambda: SQLAlchemyUsersDAO)

    uow = providers.Factory(
        UnitOfWork,
        session_factory=session_factory,
        users_dao_factory=users_dao,
    )


async def init_container() -> Container:
    container = Container()
    container.wire(
        packages=[
            "src.application.auth",
        ]
    )
    await container.init_resources()  # type: ignore[misc]
    return container


async def shutdown_container(container: Container) -> None:
    await container.shutdown_resources()  # type: ignore[misc]
    container.unwire()
