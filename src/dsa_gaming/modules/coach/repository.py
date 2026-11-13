from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dsa_gaming.modules.coach.lessons import LESSONS
from dsa_gaming.modules.coach.models import CoachMessage, LessonChunk
from dsa_gaming.modules.gameplay.models import GameAttempt, MarathonRun
from dsa_gaming.modules.identity.models import utcnow


async def ensure_lesson_rows(session: AsyncSession) -> list[LessonChunk]:
    rows = (await session.execute(select(LessonChunk))).scalars().all()
    by_slug = {row.slug: row for row in rows}
    created = False
    for item in LESSONS:
        if item["slug"] in by_slug:
            continue
        row = LessonChunk(slug=item["slug"], body=item["body"])
        session.add(row)
        by_slug[item["slug"]] = row
        created = True
    if created:
        await session.commit()
    return list(by_slug.values())


async def save_embedding(session: AsyncSession, row: LessonChunk, embedding: list[float]) -> None:
    row.embedding = embedding
    await session.commit()


async def nearest_bodies(session: AsyncSession, slug: str, vector: list[float] | None) -> list[str]:
    wanted = [slug, "shared"]
    if vector is None:
        result = await session.execute(select(LessonChunk.body).where(LessonChunk.slug.in_(wanted)))
        return [body for body in result.scalars().all()]
    result = await session.execute(
        select(LessonChunk.body)
        .where(LessonChunk.slug.in_(wanted), LessonChunk.embedding.is_not(None))
        .order_by(LessonChunk.embedding.cosine_distance(vector))
        .limit(3)
    )
    found = [body for body in result.scalars().all()]
    if found:
        return found
    result = await session.execute(select(LessonChunk.body).where(LessonChunk.slug.in_(wanted)))
    return [body for body in result.scalars().all()]


async def performance_line(session: AsyncSession, user_id: int, slug: str) -> str:
    result = await session.execute(
        select(
            func.count(GameAttempt.id),
            func.count(GameAttempt.id).filter(GameAttempt.passed.is_(True)),
            func.max(GameAttempt.score),
        )
        .join(MarathonRun, MarathonRun.id == GameAttempt.run_id)
        .where(MarathonRun.user_id == user_id, GameAttempt.slug == slug)
    )
    attempts, passed, best = result.one()
    best_score = 0 if best is None else best
    return f"Attempts {attempts} · Passed {passed} · Best score {best_score}"


async def recent_messages(session: AsyncSession, user_id: int, slug: str) -> list[CoachMessage]:
    result = await session.execute(
        select(CoachMessage)
        .where(CoachMessage.user_id == user_id, CoachMessage.slug == slug)
        .order_by(CoachMessage.id.desc())
        .limit(8)
    )
    rows = list(result.scalars().all())
    rows.reverse()
    return rows


async def add_message(session: AsyncSession, user_id: int, slug: str, role: str, content: str) -> None:
    session.add(
        CoachMessage(user_id=user_id, slug=slug, role=role, content=content[:4000], created_at=utcnow())
    )
    await session.commit()
