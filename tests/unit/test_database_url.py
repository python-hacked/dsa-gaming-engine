from dsa_gaming.core.database import asyncpg_connect


def test_neon_sslmode_becomes_asyncpg_ssl():
    url, args = asyncpg_connect(
        "postgresql+asyncpg://user:secret@host.neon.tech/dsa_gaming?sslmode=require&channel_binding=require"
    )
    assert args == {"ssl": True}
    assert "sslmode" not in url
    assert "channel_binding" not in url
    assert url.startswith("postgresql+asyncpg://user:secret@host.neon.tech/dsa_gaming")
