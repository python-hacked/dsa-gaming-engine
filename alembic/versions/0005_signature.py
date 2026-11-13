"""one founder signature for every certificate

Revision ID: 0005_signature
Revises: 0004_certificates
Create Date: 2026-11-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_signature"
down_revision: Union[str, None] = "0004_certificates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "certificate_signature",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("signer_name", sa.String(length=200), nullable=False),
        sa.Column("image", sa.LargeBinary(), nullable=False),
        sa.Column("content_type", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("certificate_signature")
