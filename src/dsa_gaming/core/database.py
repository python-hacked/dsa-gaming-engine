from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def asyncpg_connect(url: str) -> tuple[str, dict]:
    """asyncpg has no sslmode argument. Neon URLs still send it."""
    parts = urlsplit(url)
    kept: list[tuple[str, str]] = []
    ssl = None
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key == "sslmode":
            ssl = value != "disable"
            continue
        if key == "channel_binding":
            continue
        kept.append((key, value))
    cleaned = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(kept), parts.fragment))
    return cleaned, ({"ssl": ssl} if ssl is not None else {})
