import logging

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError

from dsa_gaming.modules.identity.repository import create_admin, find_admin_by_email
from dsa_gaming.modules.identity.schemas import AdminSignup
from dsa_gaming.modules.identity.service import (
    hash_password,
    record_login,
    record_logout,
    remember_google_user,
    secret_matches,
    verify_password,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["identity"])
admin_router = APIRouter(prefix="/api", tags=["admin"])

_DUMMY_HASH = "pbkdf2_sha256$200000$00000000000000000000000000000000$" + ("0" * 64)


@router.get("/google/login")
async def google_login(request: Request):
    settings = request.app.state.settings
    if not settings.google_enabled:
        return RedirectResponse("/?error=google_not_configured", status_code=303)
    return await request.app.state.oauth.google.authorize_redirect(
        request,
        settings.google_redirect_uri,
        prompt="select_account",
    )


@router.get("/google/callback")
async def google_callback(request: Request):
    if request.query_params.get("error"):
        return RedirectResponse("/?error=google_denied", status_code=303)

    try:
        token = await request.app.state.oauth.google.authorize_access_token(request)
        userinfo = token.get("userinfo")
        if not userinfo:
            userinfo = await request.app.state.oauth.google.userinfo(token=token)
    except Exception:
        logger.exception("Google sign-in failed")
        return RedirectResponse("/?error=google_failed", status_code=303)

    subject = userinfo.get("sub") if userinfo else None
    if not subject:
        return RedirectResponse("/?error=google_failed", status_code=303)

    stored = await remember_google_user(
        request,
        {
            "sub": subject,
            "email": userinfo.get("email") or "",
            "name": userinfo.get("name") or userinfo.get("email") or "Player",
            "picture": userinfo.get("picture") or "",
        },
    )
    await record_login(request, stored.get("id"))
    return RedirectResponse("/app", status_code=303)


@router.post("/admin/login")
async def admin_login(request: Request, email: str = Form(...), password: str = Form(...)):
    factory = request.app.state.sessionmaker
    if factory is None:
        return RedirectResponse("/?error=admin_database", status_code=303)
    email = email.strip().lower()
    async with factory() as db:
        user = await find_admin_by_email(db, email)
        stored_hash = user.password_hash if user and user.password_hash else _DUMMY_HASH
        password_ok = verify_password(password, stored_hash)
        if user is None or not user.password_hash or not password_ok:
            return RedirectResponse("/?error=admin_failed", status_code=303)
        await record_login(request, user.id)
        request.session["user"] = {
            "id": user.id,
            "sub": user.google_sub,
            "email": user.email,
            "name": user.name,
            "picture": user.picture or "",
            "active_language": user.active_language,
            "role": user.role,
        }
    return RedirectResponse("/app/admin", status_code=303)


@admin_router.post("/admin/signup", status_code=201)
async def admin_signup(request: Request, body: AdminSignup):
    settings = request.app.state.settings
    if not settings.admin_signup_secret:
        raise HTTPException(status_code=503, detail="Admin signup is not configured.")
    if not secret_matches(body.secret, settings.admin_signup_secret):
        raise HTTPException(status_code=401, detail="Admin signup was refused.")
    factory = request.app.state.sessionmaker
    if factory is None:
        raise HTTPException(status_code=503, detail="The database is not ready.")
    email = body.email.strip().lower()
    if "@" not in email or email.startswith("@") or len(email) > 320:
        raise HTTPException(status_code=422, detail="Enter a valid email.")
    if len(body.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters.")
    name = (body.name.strip() or email.split("@", 1)[0])[:200]
    async with factory() as db:
        if await find_admin_by_email(db, email):
            raise HTTPException(status_code=409, detail="An admin with this email already exists.")
        try:
            user = await create_admin(db, email=email, name=name, password_hash=hash_password(body.password))
        except IntegrityError:
            await db.rollback()
            raise HTTPException(status_code=409, detail="An admin with this email already exists.") from None
    return {"id": user.id, "email": user.email, "name": user.name, "role": user.role}


@router.post("/logout")
async def logout(request: Request):
    user = request.session.get("user") or {}
    await record_logout(request, user.get("id"))
    request.session.clear()
    return RedirectResponse("/", status_code=303)
