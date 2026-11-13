from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from dsa_gaming.core.database import Base
from dsa_gaming.modules.identity.models import utcnow


class MarathonRun(Base):
    __tablename__ = "marathon_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    track: Mapped[str] = mapped_column(String(16), default="dsa")
    language: Mapped[str] = mapped_column(String(32))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PuzzleRound(Base):
    __tablename__ = "puzzle_rounds"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("marathon_runs.id"), index=True)
    slug: Mapped[str] = mapped_column(String(40))
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(16), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class GameAttempt(Base):
    __tablename__ = "game_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("marathon_runs.id"), index=True)
    round_id: Mapped[int] = mapped_column(ForeignKey("puzzle_rounds.id"))
    slug: Mapped[str] = mapped_column(String(40))
    moves: Mapped[list] = mapped_column(JSON)
    score: Mapped[int] = mapped_column(default=0)
    passed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
