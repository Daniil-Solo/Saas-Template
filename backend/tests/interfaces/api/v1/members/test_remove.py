from fastapi import status

from src.constants.permissions import Permission
from tests.helpers.auth import make_token
from tests.helpers.organizations import add_member, create_organization, create_role
from tests.helpers.users import create_users


async def _member_ids(uow, organization_id: int) -> list[int]:
    async with uow.connection():
        return [member.user.id for member in await uow.members.list_for_organization(organization_id)]


async def test__success__creator_removes_member(uow, api):
    creator, member = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    member_id = await add_member(uow, organization, member)

    (await api.organizations.remove_member(organization.id, member_id, make_token(creator.id))).validate()

    assert await _member_ids(uow, organization.id) == [creator.id]


async def test__success__manager_removes_member(uow, api):
    creator, manager, member = await create_users(uow, size=3)
    organization = await create_organization(uow, creator)
    role = await create_role(uow, [Permission.MEMBERS_MANAGE])
    await add_member(uow, organization, manager, [role.id])
    member_id = await add_member(uow, organization, member)

    (await api.organizations.remove_member(organization.id, member_id, make_token(manager.id))).validate()

    assert member.id not in await _member_ids(uow, organization.id)


async def test__success__member_leaves_without_permission(uow, api):
    creator, member = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    member_id = await add_member(uow, organization, member)

    (await api.organizations.remove_member(organization.id, member_id, make_token(member.id))).validate()

    assert await _member_ids(uow, organization.id) == [creator.id]


async def test__failed__no_permission_to_remove_other(uow, api):
    creator, member, other = await create_users(uow, size=3)
    organization = await create_organization(uow, creator)
    await add_member(uow, organization, member)
    other_id = await add_member(uow, organization, other)

    (await api.organizations.remove_member(organization.id, other_id, make_token(member.id))).expected_error_status(
        status.HTTP_403_FORBIDDEN, "permission_denied"
    )

    assert other.id in await _member_ids(uow, organization.id)


async def test__failed__creator_cannot_leave(uow, api):
    creator = (await create_users(uow))[0]
    organization = await create_organization(uow, creator)
    async with uow.connection():
        creator_member_id = (await uow.members.list_for_organization(organization.id))[0].id

    (
        await api.organizations.remove_member(organization.id, creator_member_id, make_token(creator.id))
    ).expected_error_status(status.HTTP_409_CONFLICT, "organization_creator_cannot_leave")


async def test__failed__creator_cannot_be_removed_by_manager(uow, api):
    creator, manager = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    role = await create_role(uow, [Permission.MEMBERS_MANAGE])
    await add_member(uow, organization, manager, [role.id])
    async with uow.connection():
        creator_member_id = (await uow.members.list_for_organization(organization.id))[0].id

    (
        await api.organizations.remove_member(organization.id, creator_member_id, make_token(manager.id))
    ).expected_error_status(status.HTTP_409_CONFLICT, "organization_creator_cannot_leave")


async def test__failed__member_not_found(uow, api):
    creator = (await create_users(uow))[0]
    organization = await create_organization(uow, creator)

    (await api.organizations.remove_member(organization.id, 9999, make_token(creator.id))).expected_error_status(
        status.HTTP_404_NOT_FOUND, "member_not_found"
    )


async def test__failed__not_a_member(uow, api):
    creator, member, stranger = await create_users(uow, size=3)
    organization = await create_organization(uow, creator)
    member_id = await add_member(uow, organization, member)

    (await api.organizations.remove_member(organization.id, member_id, make_token(stranger.id))).expected_error_status(
        status.HTTP_404_NOT_FOUND, "organization_not_found"
    )


async def test__failed__no_authorization_header(container, api):
    (await api.organizations.remove_member(1, 1)).expected_error_status(status.HTTP_401_UNAUTHORIZED, "invalid_token")
