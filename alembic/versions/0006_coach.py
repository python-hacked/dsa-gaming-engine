"""coach lessons and private chat

Revision ID: 0006_coach
Revises: 0005_signature
Create Date: 2026-11-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0006_coach"
down_revision: Union[str, None] = "0005_signature"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "lesson_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=40), nullable=False, unique=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(768), nullable=True),
    )
    op.create_table(
        "coach_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("slug", sa.String(length=40), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_coach_messages_user_id", "coach_messages", ["user_id"])
    op.create_index("ix_coach_messages_slug", "coach_messages", ["slug"])


def downgrade() -> None:
    op.drop_index("ix_coach_messages_slug", table_name="coach_messages")
    op.drop_index("ix_coach_messages_user_id", table_name="coach_messages")
    op.drop_table("coach_messages")
    op.drop_table("lesson_chunks")
