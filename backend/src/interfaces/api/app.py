from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.application.exceptions import ApplicationError
from src.di.container import init_container, shutdown_container
from src.dto.common import ErrorDTO
from src.interfaces.api.error_status_mapping import get_status_code
from src.interfaces.api.internal import internal_router
from src.interfaces.api.v1 import v1_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    container = await init_container()
    try:
        yield
    finally:
        await shutdown_container(container)


async def application_error_handler(_: Request, error: ApplicationError) -> JSONResponse:
    status_code = get_status_code(error)
    headers = {"WWW-Authenticate": "Bearer"} if status_code == status.HTTP_401_UNAUTHORIZED else None
    body = ErrorDTO(code=error.code, message=error.message)
    return JSONResponse(status_code=status_code, content=body.model_dump(), headers=headers)


def create_app() -> FastAPI:
    app = FastAPI(title="Backend", lifespan=lifespan)
    app.add_exception_handler(ApplicationError, application_error_handler)  # type: ignore[arg-type]

    api_router = APIRouter(prefix="/api")
    api_router.include_router(v1_router)
    api_router.include_router(internal_router)
    app.include_router(api_router)
    return app


app = create_app()
