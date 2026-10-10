import sqlalchemy as sa

from src.constants.invitations import InvitationStatus

# Единые имена ограничений нужны для предсказуемых миграций и разбора ошибок БД (например, uq_users_email)
metadata = sa.MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)

users_table = sa.Table(
    "users",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("fullname", sa.String(255), nullable=False),
    sa.Column("email", sa.String(255), nullable=False, unique=True),
    sa.Column("hashed_password", sa.String(255), nullable=False),
    sa.Column("is_verified", sa.Boolean, nullable=False, server_default=sa.false()),
    sa.Column("is_admin", sa.Boolean, nullable=False, server_default=sa.false()),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
)

organizations_table = sa.Table(
    "organizations",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("name", sa.String(255), nullable=False),
    sa.Column(
        "created_by_id",
        sa.Integer,
        sa.ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    ),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
)

organization_members_table = sa.Table(
    "organization_members",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column(
        "organization_id",
        sa.Integer,
        sa.ForeignKey("organizations.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    ),
    sa.Column(
        "user_id",
        sa.Integer,
        sa.ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    ),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    sa.UniqueConstraint("organization_id", "user_id", name="uq_organization_members_organization_user"),
)

roles_table = sa.Table(
    "roles",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("name", sa.String(255), nullable=False, unique=True),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
)

role_permissions_table = sa.Table(
    "role_permissions",
    metadata,
    sa.Column(
        "role_id",
        sa.Integer,
        sa.ForeignKey("roles.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    ),
    sa.Column("permission", sa.String(64), primary_key=True),
)

member_roles_table = sa.Table(
    "member_roles",
    metadata,
    sa.Column(
        "member_id",
        sa.Integer,
        sa.ForeignKey("organization_members.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "role_id",
        sa.Integer,
        sa.ForeignKey("roles.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    ),
)

invitations_table = sa.Table(
    "invitations",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column(
        "organization_id",
        sa.Integer,
        sa.ForeignKey("organizations.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    ),
    sa.Column("email", sa.String(255), nullable=False),
    sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
    sa.Column(
        "status",
        sa.Enum(
            InvitationStatus,
            name="invitation_status",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
    ),
    sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column(
        "invited_by_id",
        sa.Integer,
        sa.ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    ),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
    sa.Index(
        "uq_invitations_pending_organization_email",
        "organization_id",
        "email",
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    ),
)

invitation_roles_table = sa.Table(
    "invitation_roles",
    metadata,
    sa.Column(
        "invitation_id",
        sa.Integer,
        sa.ForeignKey("invitations.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "role_id",
        sa.Integer,
        sa.ForeignKey("roles.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    ),
)
