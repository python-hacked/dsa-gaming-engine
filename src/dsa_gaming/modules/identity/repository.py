from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dsa_gaming.modules.identity.models import User, utcnow


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
