import factory

from src.constants.permissions import Permission
from src.dto.invitations import InvitationCreateDTO
from src.dto.organizations import OrganizationCreateDTO
from src.dto.roles import RoleCreateDTO


class OrganizationCreateFactory(factory.Factory):
    class Meta:
        model = OrganizationCreateDTO

    name = factory.Sequence(lambda n: f"Organization {n}")


class RoleCreateFactory(factory.Factory):
    class Meta:
        model = RoleCreateDTO

    name = factory.Sequence(lambda n: f"Role {n}")
    permissions = factory.LazyFunction(lambda: [Permission.MEMBERS_MANAGE])


class InvitationCreateFactory(factory.Factory):
    class Meta:
        model = InvitationCreateDTO

    email = factory.Sequence(lambda n: f"invited{n}@example.com")
    role_ids = factory.LazyFunction(list)
