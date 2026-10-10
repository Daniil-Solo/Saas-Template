import datetime

from fastapi import status

from src.constants.invitations import InvitationDisplayStatus, InvitationStatus
from src.constants.permissions import Permission
from src.constants.tasks import TaskName
from src.infrastructure.auth import invitation_token
from tests.factories.organizations import InvitationCreateFactory
from tests.helpers.auth import make_token
from tests.helpers.organizations import add_member, create_invitation, create_organization, create_role
from tests.helpers.users import create_users


async def test__success__by_creator(uow, api):
    creator = (await create_users(uow))[0]
    organization = await create_organization(uow, creator)
    role = await create_role(uow)
    data = InvitationCreateFactory.build(role_ids=[role.id])

    result = (await api.invitations.create(organization.id, data, make_token(creator.id))).validate()

    assert result.email == data.email
    assert result.status == InvitationDisplayStatus.ACTIVE
    assert [r.id for r in result.roles] == [role.id]
    assert result.invited_by_id == creator.id
    days = (result.expires_at - datetime.datetime.now(datetime.UTC)).total_seconds() / 86400
    assert 6.9 < days <= 7
    # в БД лежит только хеш токена
    async with uow.connection():
        record = await uow.invitations.get_by_token_hash(invitation_token.hash_token(result.token))
    assert record.id == result.id
    assert result.token not in str(record)


async def test__success__by_member_with_permission(uow, api):
    creator, member = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    role = await create_role(uow, [Permission.INVITATIONS_MANAGE])
    await add_member(uow, organization, member, [role.id])

    (await api.invitations.create(organization.id, InvitationCreateFactory.build(), make_token(member.id))).validate()


async def test__success__email_is_normalized(uow, api):
    creator = (await create_users(uow))[0]
    organization = await create_organization(uow, creator)

    result = (
        await api.invitations.create(
            organization.id, {"email": "  Mixed@Example.COM ", "role_ids": []}, make_token(creator.id)
        )
    ).validate()

    assert result.email == "mixed@example.com"


async def test__success__tokens_are_unique(uow, api):
    creator = (await create_users(uow))[0]
    organization = await create_organization(uow, creator)
    token = make_token(creator.id)

    first = (await api.invitations.create(organization.id, InvitationCreateFactory.build(), token)).validate()
    second = (await api.invitations.create(organization.id, InvitationCreateFactory.build(), token)).validate()

    assert first.token != second.token


async def test__success__replaces_expired_pending(uow, api):
    creator = (await create_users(uow))[0]
    organization = await create_organization(uow, creator)
    expired, _ = await create_invitation(
        uow, organization, creator, "invited@example.com", expires_in=datetime.timedelta(days=-1)
    )

    (
        await api.invitations.create(
            organization.id, InvitationCreateFactory.build(email="invited@example.com"), make_token(creator.id)
        )
    ).validate()

    async with uow.connection():
        old = await uow.invitations.get_by_id(organization.id, expired.id)
    assert old.status == InvitationStatus.REVOKED


async def test__success__after_revoked(uow, api):
    creator = (await create_users(uow))[0]
    organization = await create_organization(uow, creator)
    await create_invitation(uow, organization, creator, "invited@example.com", status=InvitationStatus.REVOKED)

    (
        await api.invitations.create(
            organization.id, InvitationCreateFactory.build(email="invited@example.com"), make_token(creator.id)
        )
    ).validate()


async def test__failed__active_invitation_exists(uow, api):
    creator = (await create_users(uow))[0]
    organization = await create_organization(uow, creator)
    await create_invitation(uow, organization, creator, "invited@example.com")

    (
        await api.invitations.create(
            organization.id, InvitationCreateFactory.build(email="INVITED@example.com"), make_token(creator.id)
        )
    ).expected_error_status(status.HTTP_409_CONFLICT, "invitation_already_exists")


async def test__failed__already_member(uow, api):
    creator, member = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    await add_member(uow, organization, member)

    (
        await api.invitations.create(
            organization.id, InvitationCreateFactory.build(email=member.email), make_token(creator.id)
        )
    ).expected_error_status(status.HTTP_409_CONFLICT, "member_already_exists")


async def test__failed__role_not_found(uow, api):
    creator = (await create_users(uow))[0]
    organization = await create_organization(uow, creator)

    (
        await api.invitations.create(
            organization.id, InvitationCreateFactory.build(role_ids=[9999]), make_token(creator.id)
        )
    ).expected_error_status(status.HTTP_404_NOT_FOUND, "role_not_found")


async def test__failed__no_permission(uow, api):
    creator, member = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    role = await create_role(uow, [Permission.MEMBERS_MANAGE])
    await add_member(uow, organization, member, [role.id])

    (
        await api.invitations.create(organization.id, InvitationCreateFactory.build(), make_token(member.id))
    ).expected_error_status(status.HTTP_403_FORBIDDEN, "permission_denied")


async def test__failed__not_a_member(uow, api):
    creator, stranger = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)

    (
        await api.invitations.create(organization.id, InvitationCreateFactory.build(), make_token(stranger.id))
    ).expected_error_status(status.HTTP_404_NOT_FOUND, "organization_not_found")


async def test__failed__invalid_email(uow, api):
    creator = (await create_users(uow))[0]
    organization = await create_organization(uow, creator)

    (
        await api.invitations.create(organization.id, {"email": "not-an-email", "role_ids": []}, make_token(creator.id))
    ).expect_validation_error(field="email")


async def test__failed__no_authorization_header(container, api):
    (await api.invitations.create(1, InvitationCreateFactory.build())).expected_error_status(
        status.HTTP_401_UNAUTHORIZED, "invalid_token"
    )


async def test__success__email_task_is_enqueued(uow, api, task_queue):
    creator = (await create_users(uow))[0]
    organization = await create_organization(uow, creator)

    result = (
        await api.invitations.create(organization.id, InvitationCreateFactory.build(), make_token(creator.id))
    ).validate()

    assert len(task_queue.tasks) == 1
    task = task_queue.tasks[0]
    assert task.task == TaskName.SEND_INVITATION_EMAIL
    assert task.job_id == f"invitation-{result.id}"
    assert task.payload.invitation_id == result.id
    assert task.payload.token == result.token
    assert result.token not in repr(task.payload)


async def test__failed__already_member_enqueues_nothing(uow, api, task_queue):
    creator, member = await create_users(uow, size=2)
    organization = await create_organization(uow, creator)
    await add_member(uow, organization, member)

    (
        await api.invitations.create(
            organization.id, InvitationCreateFactory.build(email=member.email), make_token(creator.id)
        )
    ).expected_error_status(status.HTTP_409_CONFLICT, "member_already_exists")

    assert task_queue.tasks == []
