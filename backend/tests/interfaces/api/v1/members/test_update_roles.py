from fastapi import status

from src.constants.permissions import Permission
from src.dto.organizations import MemberRolesUpdateDTO
from tests.helpers.auth import make_token
from tests.helpers.organizations import add_member, create_organization, create_role
from tests.helpers.users import create_users


async def test__success__by_creator(uow, api):
    creator, member = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    old_role = await create_role(uow)
    new_role = await create_role(uow, [Permission.INVITATIONS_MANAGE])
    member_id = await add_member(uow, organization, member, [old_role.id])

    result = (
        await api.organizations.update_member_roles(
            organization.id, member_id, MemberRolesUpdateDTO(role_ids=[new_role.id]), make_token(creator.id)
        )
    ).validate()

    assert [role.id for role in result.roles] == [new_role.id]


async def test__success__by_member_with_permission(uow, api):
    creator, manager, member = await create_users(uow, size=3)
    organization = await create_organization(uow, creator)
    manage_role = await create_role(uow, [Permission.MEMBERS_MANAGE])
    # назначить можно роль с правами, которых нет у самого менеджера
    strong_role = await create_role(uow, [Permission.INVITATIONS_MANAGE])
    await add_member(uow, organization, manager, [manage_role.id])
    member_id = await add_member(uow, organization, member)

    result = (
        await api.organizations.update_member_roles(
            organization.id, member_id, MemberRolesUpdateDTO(role_ids=[strong_role.id]), make_token(manager.id)
        )
    ).validate()

    assert [role.id for role in result.roles] == [strong_role.id]


async def test__success__clear_roles(uow, api):
    creator, member = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    role = await create_role(uow)
    member_id = await add_member(uow, organization, member, [role.id])

    result = (
        await api.organizations.update_member_roles(
            organization.id, member_id, MemberRolesUpdateDTO(role_ids=[]), make_token(creator.id)
        )
    ).validate()

    assert result.roles == []


async def test__success__duplicate_role_ids(uow, api):
    creator, member = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    role = await create_role(uow)
    member_id = await add_member(uow, organization, member)

    result = (
        await api.organizations.update_member_roles(
            organization.id, member_id, MemberRolesUpdateDTO(role_ids=[role.id, role.id]), make_token(creator.id)
        )
    ).validate()

    assert [r.id for r in result.roles] == [role.id]


async def test__failed__no_permission(uow, api):
    creator, member, other = await create_users(uow, size=3)
    organization = await create_organization(uow, creator)
    invite_role = await create_role(uow, [Permission.INVITATIONS_MANAGE])
    await add_member(uow, organization, member, [invite_role.id])
    other_id = await add_member(uow, organization, other)

    (
        await api.organizations.update_member_roles(
            organization.id, other_id, MemberRolesUpdateDTO(role_ids=[]), make_token(member.id)
        )
    ).expected_error_status(status.HTTP_403_FORBIDDEN, "permission_denied")


async def test__failed__not_a_member(uow, api):
    creator, member, stranger = await create_users(uow, size=3)
    organization = await create_organization(uow, creator)
    member_id = await add_member(uow, organization, member)

    (
        await api.organizations.update_member_roles(
            organization.id, member_id, MemberRolesUpdateDTO(role_ids=[]), make_token(stranger.id)
        )
    ).expected_error_status(status.HTTP_404_NOT_FOUND, "organization_not_found")


async def test__failed__member_not_found(uow, api):
    creator = (await create_users(uow))[0]
    organization = await create_organization(uow, creator)

    (
        await api.organizations.update_member_roles(
            organization.id, 9999, MemberRolesUpdateDTO(role_ids=[]), make_token(creator.id)
        )
    ).expected_error_status(status.HTTP_404_NOT_FOUND, "member_not_found")


async def test__failed__member_of_other_organization(uow, api):
    creator, other_creator = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    other_organization = await create_organization(uow, other_creator)
    async with uow.connection():
        other_members = await uow.members.list_for_organization(other_organization.id)

    (
        await api.organizations.update_member_roles(
            organization.id, other_members[0].id, MemberRolesUpdateDTO(role_ids=[]), make_token(creator.id)
        )
    ).expected_error_status(status.HTTP_404_NOT_FOUND, "member_not_found")


async def test__failed__role_not_found(uow, api):
    creator, member = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    member_id = await add_member(uow, organization, member)

    (
        await api.organizations.update_member_roles(
            organization.id, member_id, MemberRolesUpdateDTO(role_ids=[9999]), make_token(creator.id)
        )
    ).expected_error_status(status.HTTP_404_NOT_FOUND, "role_not_found")


async def test__failed__invalid_payload(uow, api):
    creator = (await create_users(uow))[0]
    organization = await create_organization(uow, creator)

    (
        await api.organizations.update_member_roles(organization.id, 1, {"role_ids": "x"}, make_token(creator.id))
    ).expect_validation_error()


async def test__failed__no_authorization_header(container, api):
    (await api.organizations.update_member_roles(1, 1, MemberRolesUpdateDTO(role_ids=[]))).expected_error_status(
        status.HTTP_401_UNAUTHORIZED, "invalid_token"
    )
