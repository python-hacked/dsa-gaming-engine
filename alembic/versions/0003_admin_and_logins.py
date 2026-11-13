"""admin role, certificate grant, and login sessions

Revision ID: 0003_admin_and_logins
Revises: 0002_marathon_and_rounds
Create Date: 2026-11-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_admin_and_logins"
down_revision: Union[str, None] = "0002_marathon_and_rounds"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("role", sa.String(length=16), nullable=False, server_default="player"))
    op.add_column("users", sa.Column("password_hash", sa.String(length=255), nullable=True))
    op.add_column(
        "users",
        sa.Column("certificate_unlocked", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("users", sa.Column("certificate_unlocked_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table(
        "login_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_login_sessions_user_id", "login_sessions", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_login_sessions_user_id", table_name="login_sessions")
    op.drop_table("login_sessions")
    op.drop_column("users", "certificate_unlocked_at")
    op.drop_column("users", "certificate_unlocked")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "role")
