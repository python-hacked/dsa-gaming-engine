from authlib.integrations.starlette_client import OAuth
from fastapi import Request

from dsa_gaming.core.config import Settings
from dsa_gaming.modules.identity.repository import set_active_language, upsert_google_user


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
    request.session["user"] = stored
    return stored


async def remember_language(request: Request, language: str) -> None:
    user = dict(request.session.get("user") or {})
    user["active_language"] = language
    request.session["user"] = user
    factory = request.app.state.sessionmaker
    if factory is not None and user.get("sub"):
        async with factory() as db:
            await set_active_language(db, user["sub"], language)
