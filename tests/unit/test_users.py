import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from dsa_gaming.core.database import Base
from dsa_gaming.modules.identity.repository import upsert_google_user


@pytest.mark.asyncio
async def test_google_user_is_saved_once():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as db:
        created = await upsert_google_user(
            db,
            google_sub="google-1",
            email="satish@example.com",
            name="Satish",
            picture="",
        )
        renamed = await upsert_google_user(
            db,
            google_sub="google-1",
            email="satish@example.com",
            name="Satish K",
            picture="",
        )
    assert created.id == renamed.id
    assert renamed.name == "Satish K"
    await engine.dispose()
