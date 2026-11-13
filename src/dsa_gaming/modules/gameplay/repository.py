from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dsa_gaming.modules.gameplay.models import GameAttempt, MarathonRun, PuzzleRound
from dsa_gaming.modules.gameplay.service import PLAYABLE, deadline, new_puzzle
from dsa_gaming.modules.identity.models import utcnow


async def active_run(session: AsyncSession, user_id: int, now: datetime | None = None) -> MarathonRun | None:
    now = now or utcnow()
    result = await session.execute(
        select(MarathonRun)
        .where(MarathonRun.user_id == user_id, MarathonRun.expires_at > now)
        .order_by(MarathonRun.id.desc())
    )
    return result.scalars().first()


async def start_run(session: AsyncSession, user_id: int, language: str) -> MarathonRun:
    current = await active_run(session, user_id)
    if current is not None:
        return current
    now = utcnow()
    run = MarathonRun(user_id=user_id, track="dsa", language=language, started_at=now, expires_at=deadline(now))
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return run


async def cleared_slugs(session: AsyncSession, run_id: int) -> set[str]:
    result = await session.execute(
        select(GameAttempt.slug).where(GameAttempt.run_id == run_id, GameAttempt.passed.is_(True))
    )
    return set(result.scalars().all())


async def open_round(session: AsyncSession, run_id: int, slug: str) -> PuzzleRound | None:
    result = await session.execute(
        select(PuzzleRound)
        .where(PuzzleRound.run_id == run_id, PuzzleRound.slug == slug, PuzzleRound.status == "open")
        .order_by(PuzzleRound.id.desc())
    )
    return result.scalars().first()


async def begin_round(session: AsyncSession, run_id: int, slug: str, fresh: bool = False) -> PuzzleRound:
    if slug not in PLAYABLE:
        raise KeyError(slug)
    if not fresh:
        existing = await open_round(session, run_id, slug)
        if existing is not None:
            return existing
    puzzle = PuzzleRound(run_id=run_id, slug=slug, payload=new_puzzle(slug), status="open")
    session.add(puzzle)
    await session.commit()
    await session.refresh(puzzle)
    return puzzle


async def get_round(session: AsyncSession, round_id: int, run_id: int) -> PuzzleRound | None:
    result = await session.execute(
        select(PuzzleRound).where(PuzzleRound.id == round_id, PuzzleRound.run_id == run_id)
    )
    return result.scalar_one_or_none()


async def save_attempt(
    session: AsyncSession,
    puzzle: PuzzleRound,
    moves: list,
    score: int,
    passed: bool,
) -> GameAttempt:
    attempt = GameAttempt(
        run_id=puzzle.run_id,
        round_id=puzzle.id,
        slug=puzzle.slug,
        moves=moves,
        score=score,
        passed=passed,
    )
    if passed:
        puzzle.status = "passed"
    session.add(attempt)
    await session.commit()
    await session.refresh(attempt)
    return attempt
