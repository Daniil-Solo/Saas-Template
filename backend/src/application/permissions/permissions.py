from src.constants.permissions import Permission


async def get_all() -> list[Permission]:
    return list(Permission)
