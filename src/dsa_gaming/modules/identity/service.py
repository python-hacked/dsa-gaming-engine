import hashlib
import hmac
import secrets

from authlib.integrations.starlette_client import OAuth
from fastapi import Request

from dsa_gaming.core.config import Settings
from dsa_gaming.modules.identity.repository import (
    begin_login,
    end_login,
    set_active_language,
    upsert_google_user,
)

_PASSWORD_ROUNDS = 200_000


def build_oauth(settings: Settings) -> OAuth:
    oauth = OAuth()
    if settings.google_enabled:
        oauth.register(
            name="google",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
    return oauth


async def remember_google_user(request: Request, profile: dict) -> dict:
    stored = {
        "sub": profile["sub"],
        "email": profile.get("email") or "",
        "name": profile.get("name") or profile.get("email") or "Player",
        "picture": profile.get("picture") or "",
        "active_language": profile.get("active_language"),
    }
    factory = request.app.state.sessionmaker
    if factory is not None:
        async with factory() as db:
            saved = await upsert_google_user(
                db,
                google_sub=stored["sub"],
                email=stored["email"],
                name=stored["name"],
                picture=stored["picture"],
            )
            stored["id"] = saved.id
            stored["active_language"] = saved.active_language
            stored["role"] = saved.role
    stored.setdefault("role", "player")
    request.session["user"] = stored
    return stored


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), _PASSWORD_ROUNDS)
    return f"pbkdf2_sha256${_PASSWORD_ROUNDS}${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, rounds, salt, digest = stored.split("$", 3)
        count = int(rounds)
    except ValueError:
        return False
    if algo != "pbkdf2_sha256" or count < 1:
        return False
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), count).hex()
    return hmac.compare_digest(check, digest)


def secret_matches(given: str, expected: str) -> bool:
    if not given or not expected:
        return False
    return hmac.compare_digest(
        hashlib.sha256(given.encode()).digest(),
        hashlib.sha256(expected.encode()).digest(),
    )


async def record_login(request: Request, user_id: int | None) -> None:
    factory = request.app.state.sessionmaker
    if factory is None or not user_id:
        return
    async with factory() as db:
        await begin_login(db, user_id)


async def record_logout(request: Request, user_id: int | None) -> None:
    factory = request.app.state.sessionmaker
    if factory is None or not user_id:
        return
    async with factory() as db:
        await end_login(db, user_id)


async def remember_language(request: Request, language: str) -> None:
    user = dict(request.session.get("user") or {})
    user["active_language"] = language
    request.session["user"] = user
    factory = request.app.state.sessionmaker
    if factory is not None and user.get("sub"):
        async with factory() as db:
            await set_active_language(db, user["sub"], language)
