import hashlib
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dsa_gaming.modules.gameplay.models import GameAttempt, MarathonRun
from dsa_gaming.modules.identity.models import LoginSession, User, utcnow


async def upsert_google_user(
    session: AsyncSession,
    *,
    google_sub: str,
    email: str,
    name: str,
    picture: str,
) -> User:
    result = await session.execute(select(User).where(User.google_sub == google_sub))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(google_sub=google_sub, email=email, name=name, picture=picture)
        session.add(user)
    else:
        user.email = email
        user.name = name
        user.picture = picture
        user.updated_at = utcnow()
    await session.commit()
    await session.refresh(user)
    return user


async def set_active_language(session: AsyncSession, google_sub: str, language: str) -> User | None:
    result = await session.execute(select(User).where(User.google_sub == google_sub))
    user = result.scalar_one_or_none()
    if user is None:
        return None
    user.active_language = language
    user.updated_at = utcnow()
    await session.commit()
    await session.refresh(user)
    return user


def admin_subject(email: str) -> str:
    return "admin:" + hashlib.sha256(email.encode()).hexdigest()


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def find_admin_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email, User.role == "admin"))
    return result.scalar_one_or_none()


async def create_admin(
    session: AsyncSession,
    *,
    email: str,
    name: str,
    password_hash: str,
) -> User:
    user = User(
        google_sub=admin_subject(email),
        email=email,
        name=name,
        picture="",
        role="admin",
        password_hash=password_hash,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def begin_login(session: AsyncSession, user_id: int) -> None:
    now = utcnow()
    result = await session.execute(
        select(LoginSession).where(LoginSession.user_id == user_id, LoginSession.ended_at.is_(None))
    )
    for row in result.scalars():
        row.ended_at = now
    session.add(LoginSession(user_id=user_id, started_at=now))
    await session.commit()


async def end_login(session: AsyncSession, user_id: int) -> None:
    now = utcnow()
    result = await session.execute(
        select(LoginSession).where(LoginSession.user_id == user_id, LoginSession.ended_at.is_(None))
    )
    rows = result.scalars().all()
    if not rows:
        return
    for row in rows:
        row.ended_at = now
    await session.commit()


async def unlock_certificate(session: AsyncSession, user_id: int) -> User | None:
    user = await get_user(session, user_id)
    if user is None:
        return None
    if not user.certificate_unlocked:
        user.certificate_unlocked = True
        user.certificate_unlocked_at = utcnow()
        user.updated_at = utcnow()
        await session.commit()
        await session.refresh(user)
    return user


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _stamp(value: datetime) -> str:
    return _aware(value).astimezone(timezone.utc).strftime("%d %b %Y, %H:%M UTC")


def _length(seconds: int) -> str:
    seconds = max(0, int(seconds))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m"
    return f"{secs}s"


def _span(started: datetime, ended: datetime | None, now: datetime) -> int:
    return max(0, int((_aware(ended or now) - _aware(started)).total_seconds()))


async def user_reports(session: AsyncSession) -> list[dict]:
    now = utcnow()
    users = (await session.execute(select(User).order_by(User.id.desc()))).scalars().all()
    if not users:
        return []
    ids = [user.id for user in users]
    visits = (
        await session.execute(select(LoginSession).where(LoginSession.user_id.in_(ids)))
    ).scalars().all()
    attempts = (
        await session.execute(
            select(
                MarathonRun.user_id,
                MarathonRun.id.label("run_id"),
                GameAttempt.slug,
                GameAttempt.passed,
            )
            .join(GameAttempt, GameAttempt.run_id == MarathonRun.id)
            .where(MarathonRun.user_id.in_(ids))
        )
    ).all()
    active_runs = (
        await session.execute(
            select(MarathonRun.user_id, MarathonRun.id).where(
                MarathonRun.user_id.in_(ids),
                MarathonRun.expires_at > now,
            )
        )
    ).all()
    active_by_user: dict[int, set[int]] = {user_id: set() for user_id in ids}
    for row in active_runs:
        active_by_user.setdefault(row.user_id, set()).add(row.id)
    by_user_visits: dict[int, list[LoginSession]] = {user_id: [] for user_id in ids}
    for visit in visits:
        by_user_visits.setdefault(visit.user_id, []).append(visit)
    by_user_attempts: dict[int, list] = {user_id: [] for user_id in ids}
    for row in attempts:
        by_user_attempts.setdefault(row.user_id, []).append(row)

    reports = []
    for user in users:
        history = sorted(by_user_visits.get(user.id, []), key=lambda row: _aware(row.started_at), reverse=True)
        total_seconds = sum(_span(row.started_at, row.ended_at, now) for row in history)
        passed = [row for row in by_user_attempts.get(user.id, []) if row.passed]
        active_ids = active_by_user.get(user.id, set())
        sitting = None
        if active_ids:
            sitting = len({row.slug for row in passed if row.run_id in active_ids})
        reports.append(
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "picture": user.picture or "",
                "role": user.role,
                "language": user.active_language or "",
                "joined": _stamp(user.created_at),
                "tasks": len({row.slug for row in passed}),
                "attempts": len(passed),
                "sitting": sitting,
                "online": any(row.ended_at is None for row in history),
                "time_online": _length(total_seconds),
                "logins": len(history),
                "visits": [
                    {
                        "when": _stamp(row.started_at),
                        "length": _length(_span(row.started_at, row.ended_at, now)),
                        "open": row.ended_at is None,
                    }
                    for row in history[:5]
                ],
                "certificate_unlocked": user.certificate_unlocked,
            }
        )
    return reports
