"""one certificate per programming language

Revision ID: 0004_certificates
Revises: 0003_admin_and_logins
Create Date: 2026-11-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_certificates"
down_revision: Union[str, None] = "0003_admin_and_logins"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "certificates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("language", sa.String(length=32), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_certificates_public_id", "certificates", ["public_id"], unique=True)
    op.create_index("ix_certificates_user_id", "certificates", ["user_id"])
    op.create_unique_constraint("uq_certificates_user_language", "certificates", ["user_id", "language"])


def downgrade() -> None:
    op.drop_constraint("uq_certificates_user_language", "certificates", type_="unique")
    op.drop_index("ix_certificates_user_id", table_name="certificates")
    op.drop_index("ix_certificates_public_id", table_name="certificates")
    op.drop_table("certificates")
