"""marathon runs, puzzle rounds, and attempts

Revision ID: 0002_marathon_and_rounds
Revises: 0001_create_users
Create Date: 2026-11-12
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_marathon_and_rounds"
down_revision: Union[str, None] = "0001_create_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "marathon_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("track", sa.String(length=16), nullable=False),
        sa.Column("language", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_marathon_runs_user_id", "marathon_runs", ["user_id"])
    op.create_table(
        "puzzle_rounds",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("marathon_runs.id"), nullable=False),
        sa.Column("slug", sa.String(length=40), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_puzzle_rounds_run_id", "puzzle_rounds", ["run_id"])
    op.create_table(
        "game_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("marathon_runs.id"), nullable=False),
        sa.Column("round_id", sa.Integer(), sa.ForeignKey("puzzle_rounds.id"), nullable=False),
        sa.Column("slug", sa.String(length=40), nullable=False),
        sa.Column("moves", sa.JSON(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_game_attempts_run_id", "game_attempts", ["run_id"])


def downgrade() -> None:
    op.drop_index("ix_game_attempts_run_id", table_name="game_attempts")
    op.drop_table("game_attempts")
    op.drop_index("ix_puzzle_rounds_run_id", table_name="puzzle_rounds")
    op.drop_table("puzzle_rounds")
    op.drop_index("ix_marathon_runs_user_id", table_name="marathon_runs")
    op.drop_table("marathon_runs")
