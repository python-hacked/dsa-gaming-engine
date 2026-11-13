import logging

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from dsa_gaming.modules.identity.service import remember_google_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["identity"])


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

    await remember_google_user(
        request,
        {
            "sub": subject,
            "email": userinfo.get("email") or "",
            "name": userinfo.get("name") or userinfo.get("email") or "Player",
            "picture": userinfo.get("picture") or "",
        },
    )
    return RedirectResponse("/app", status_code=303)


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)
