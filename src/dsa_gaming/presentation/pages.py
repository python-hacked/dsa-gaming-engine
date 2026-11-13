import json
from pathlib import Path

from fastapi import APIRouter, File, Form, Request, UploadFile
from markupsafe import Markup
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from dsa_gaming.modules.catalog.data import DSA_GAMES, LANGUAGE_IDS, LANGUAGES, SQL_TASKS, editor_language
from dsa_gaming.modules.certificates.pdf import build_certificate_pdf, pdf_filename
from dsa_gaming.modules.certificates.repository import (
    certificate_by_public_id,
    certificate_cards,
    get_signature,
    issue_certificate,
    issued_language_map,
    save_signature,
)
from dsa_gaming.modules.certificates.service import format_issued, linkedin_url
from dsa_gaming.modules.certificates.signature import SignatureError, decode_drawn, normalize_signature
from dsa_gaming.modules.gameplay.repository import active_run, begin_round, cleared_slugs, start_run, use_language
from dsa_gaming.modules.gameplay.service import PLAYABLE, clock_label, public_payload
from dsa_gaming.modules.identity.models import User, utcnow
from dsa_gaming.modules.identity.repository import user_reports
from dsa_gaming.modules.identity.service import remember_google_user, remember_language
from dsa_gaming.modules.runner.starters import build_starter

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

router = APIRouter(tags=["pages"])

LOGIN_ERRORS = {
    "google_not_configured": "Google sign-in needs a client id and secret in .env. Add them, then restart the app.",
    "google_denied": "Google sign-in was cancelled.",
    "google_failed": "Google sign-in did not finish. Try again.",
    "database": "The marathon needs Postgres running. Start it, then try again.",
    "language": "Choose a language before starting the marathon.",
    "admin_failed": "That admin email or password is wrong.",
    "admin_database": "Admin sign-in needs Postgres running. Start it, then try again.",
}

SIGNATURE_NOTICES = {
    "saved": "Signature saved. It is on every certificate.",
    "signature": "Draw a signature or upload one image.",
    "signature_type": "Use a PNG, JPEG, or WebP image under 1.5 MB.",
}


def _language_name(code: str | None) -> str:
    for language_id, name in LANGUAGES:
        if language_id == code:
            return name
    return ""


def _game(slug: str) -> dict | None:
    return next((game for game in DSA_GAMES if game["slug"] == slug), None)


def _next_href(slug: str) -> str:
    slugs = [game["slug"] for game in DSA_GAMES]
    try:
        index = slugs.index(slug)
    except ValueError:
        return "/app/dsa"
    if index + 1 >= len(slugs):
        return "/app/dsa"
    return f"/play/{slugs[index + 1]}?new=1"


async def _marathon(request: Request, user: dict) -> dict | None:
    factory = request.app.state.sessionmaker
    if factory is None or not user.get("id"):
        return None
    async with factory() as session:
        run = await active_run(session, user["id"])
        if run is None:
            return None
        cleared = await cleared_slugs(session, run.id)
    return {
        "id": run.id,
        "language": run.language,
        "expires_at": run.expires_at.isoformat(),
        "label": clock_label(run.expires_at, utcnow()),
        "cleared": cleared,
    }


async def _player(request: Request) -> dict | None:
    user = request.session.get("user")
    if not user:
        return None
    if request.app.state.sessionmaker is None:
        return user
    return await remember_google_user(request, user)


@router.get("/")
async def login_page(request: Request):
    code = request.query_params.get("error")
    return TEMPLATES.TemplateResponse(
        request,
        "landing.html",
        {
            "error": LOGIN_ERRORS.get(code or "", ""),
            "user": request.session.get("user"),
            "admin_open": code in {"admin_failed", "admin_database"},
        },
    )


@router.get("/app")
async def app_home(request: Request):
    user = await _player(request)
    if not user:
        return RedirectResponse("/", status_code=303)
    return TEMPLATES.TemplateResponse(
        request,
        "dashboard.html",
        {
            "user": user,
            "language_name": _language_name(user.get("active_language")),
        },
    )


@router.get("/app/dsa")
async def dsa_track(request: Request):
    user = await _player(request)
    if not user:
        return RedirectResponse("/", status_code=303)
    code = request.query_params.get("notice")
    marathon = await _marathon(request, user)
    return TEMPLATES.TemplateResponse(
        request,
        "dsa.html",
        {
            "user": user,
            "languages": LANGUAGES,
            "games": DSA_GAMES,
            "language_name": _language_name(user.get("active_language")),
            "playable": PLAYABLE,
            "marathon": marathon,
            "notice": LOGIN_ERRORS.get(code or "", ""),
        },
    )


@router.post("/app/dsa/marathon")
async def begin_marathon(request: Request):
    user = await _player(request)
    if not user:
        return RedirectResponse("/", status_code=303)
    if not user.get("active_language"):
        return RedirectResponse("/app/dsa?notice=language", status_code=303)
    factory = request.app.state.sessionmaker
    if factory is None or not user.get("id"):
        return RedirectResponse("/app/dsa?notice=database", status_code=303)
    async with factory() as session:
        await start_run(session, user["id"], user["active_language"])
    return RedirectResponse("/app/dsa", status_code=303)


@router.get("/play/{slug}")
async def play_game(request: Request, slug: str, new: int = 0):
    user = await _player(request)
    if not user:
        return RedirectResponse("/", status_code=303)
    game = _game(slug)
    if game is None:
        return RedirectResponse("/app/dsa", status_code=303)
    factory = request.app.state.sessionmaker
    if factory is None or not user.get("id"):
        return RedirectResponse("/app/dsa?notice=database", status_code=303)
    async with factory() as session:
        run = await active_run(session, user["id"])
        if run is None:
            return RedirectResponse("/app/dsa", status_code=303)
        expires_at = run.expires_at
        language = await use_language(session, run, editor_language(user.get("active_language"), run.language))
        if slug not in PLAYABLE:
            return TEMPLATES.TemplateResponse(
                request,
                "soon.html",
                {
                    "user": user,
                    "title": game["title"],
                    "topic": game["topic"],
                    "par": game["par"],
                    "next_href": _next_href(slug),
                    "expires_at": expires_at.isoformat(),
                    "label": clock_label(expires_at, utcnow()),
                },
            )
        puzzle = await begin_round(session, run.id, slug, fresh=bool(new))
        round_id = puzzle.id
        shown = public_payload(puzzle.payload)
        cleared = puzzle.status == "passed"
    return TEMPLATES.TemplateResponse(
        request,
        "play.html",
        {
            "user": user,
            "slug": slug,
            "title": game["title"],
            "round_id": round_id,
            "puzzle_json": Markup(json.dumps(shown)),
            "starter": build_starter(slug, language, shown),
            "language_name": _language_name(language),
            "expires_at": expires_at.isoformat(),
            "label": clock_label(expires_at, utcnow()),
            "next_href": _next_href(slug),
            "cleared": cleared,
        },
    )


@router.post("/app/dsa/language")
async def choose_language(request: Request, language: str = Form(...)):
    user = await _player(request)
    if not user:
        return RedirectResponse("/", status_code=303)
    if language in LANGUAGE_IDS:
        await remember_language(request, language)
    return RedirectResponse("/app/dsa", status_code=303)


def _progress(cleared: set[str]) -> tuple[int, int]:
    slugs = [game["slug"] for game in DSA_GAMES]
    return len(set(slugs) & cleared), len(slugs)


def _require_admin(user: dict | None) -> RedirectResponse | None:
    if not user:
        return RedirectResponse("/", status_code=303)
    if user.get("role") != "admin":
        return RedirectResponse("/app", status_code=303)
    return None


def _pdf_response(
    name: str,
    language_name: str,
    issued_on: str,
    public_id: str,
    signature: bytes | None,
    signer_name: str,
) -> Response:
    payload = build_certificate_pdf(name, language_name, issued_on, public_id, signature, signer_name)
    filename = pdf_filename(name, language_name)
    return Response(
        content=payload,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


async def _signature_context(request: Request) -> dict:
    factory = request.app.state.sessionmaker
    if factory is None:
        return {"present": False, "name": "", "src": ""}
    async with factory() as session:
        row = await get_signature(session)
    if row is None:
        return {"present": False, "name": "", "src": ""}
    return {"present": True, "name": row.signer_name, "src": "/signature"}


async def _signature_file(request: Request) -> tuple[bytes | None, str]:
    factory = request.app.state.sessionmaker
    if factory is None:
        return None, ""
    async with factory() as session:
        row = await get_signature(session)
    if row is None:
        return None, ""
    return row.image, row.signer_name


async def _cards(request: Request, user: dict) -> list[dict]:
    factory = request.app.state.sessionmaker
    if factory is None or not user.get("id"):
        code = user.get("active_language") or "python"
        return [
            {
                "language": code,
                "language_name": _language_name(code) or "Python",
                "ready": False,
                "issued_on": "",
                "public_id": "",
                "download_href": "",
                "share_href": "",
                "open_href": "",
            }
        ]
    async with factory() as session:
        row = await session.get(User, int(user["id"]))
        if row is None:
            return []
        return await certificate_cards(session, row, request.app.state.settings.app_base_url)


@router.get("/app/profile")
async def profile(request: Request):
    user = await _player(request)
    if not user:
        return RedirectResponse("/", status_code=303)
    marathon = await _marathon(request, user)
    cleared = marathon["cleared"] if marathon else set()
    done, total = _progress(cleared)
    return TEMPLATES.TemplateResponse(
        request,
        "profile.html",
        {
            "user": user,
            "language_name": _language_name((marathon or {}).get("language") or user.get("active_language")),
            "done": done,
            "total": total,
            "certificates": await _cards(request, user),
            "signature": await _signature_context(request),
        },
    )


@router.get("/app/certificate")
async def certificate_home(request: Request):
    user = await _player(request)
    if not user:
        return RedirectResponse("/", status_code=303)
    cards = await _cards(request, user)
    ready = next((card for card in cards if card["ready"]), None)
    if ready is None:
        return RedirectResponse("/app/profile", status_code=303)
    return RedirectResponse(ready["open_href"], status_code=303)


@router.get("/app/certificate/{public_id}")
async def certificate_page(request: Request, public_id: str):
    user = await _player(request)
    if not user:
        return RedirectResponse("/", status_code=303)
    factory = request.app.state.sessionmaker
    if factory is None:
        return RedirectResponse("/app/profile", status_code=303)
    async with factory() as session:
        found = await certificate_by_public_id(session, public_id)
    if found is None or found[0].user_id != int(user.get("id") or 0):
        return RedirectResponse("/app/profile", status_code=303)
    cert, holder = found
    language_name = _language_name(cert.language) or cert.language
    issued_on = format_issued(cert.issued_at)
    signature = await _signature_context(request)
    return TEMPLATES.TemplateResponse(
        request,
        "certificate.html",
        {
            "user": user,
            "holder_name": holder.name,
            "language_name": language_name,
            "issued_on": issued_on,
            "cert_id": cert.public_id,
            "signature": signature,
            "download_href": f"/app/certificate/{cert.public_id}/download",
            "share_href": linkedin_url(
                request.app.state.settings.app_base_url, cert.public_id, language_name, cert.issued_at
            ),
        },
    )


@router.get("/app/certificate/{public_id}/download")
async def download_certificate(request: Request, public_id: str):
    user = await _player(request)
    if not user:
        return RedirectResponse("/", status_code=303)
    factory = request.app.state.sessionmaker
    if factory is None:
        return RedirectResponse("/app/profile", status_code=303)
    async with factory() as session:
        found = await certificate_by_public_id(session, public_id)
    if found is None or found[0].user_id != int(user.get("id") or 0):
        return RedirectResponse("/app/profile", status_code=303)
    cert, holder = found
    language_name = _language_name(cert.language) or cert.language
    image, signer_name = await _signature_file(request)
    return _pdf_response(holder.name, language_name, format_issued(cert.issued_at), cert.public_id, image, signer_name)


@router.get("/verify/{public_id}")
async def verify_certificate(request: Request, public_id: str):
    factory = request.app.state.sessionmaker
    if factory is None:
        return RedirectResponse("/", status_code=303)
    async with factory() as session:
        found = await certificate_by_public_id(session, public_id)
    if found is None:
        return RedirectResponse("/", status_code=303)
    cert, holder = found
    language_name = _language_name(cert.language) or cert.language
    issued_on = format_issued(cert.issued_at)
    return TEMPLATES.TemplateResponse(
        request,
        "verify.html",
        {
            "holder_name": holder.name,
            "language_name": language_name,
            "issued_on": issued_on,
            "cert_id": cert.public_id,
            "signature": await _signature_context(request),
            "download_href": f"/verify/{cert.public_id}/download",
            "share_href": linkedin_url(
                request.app.state.settings.app_base_url, cert.public_id, language_name, cert.issued_at
            ),
        },
    )


@router.get("/verify/{public_id}/download")
async def download_public_certificate(request: Request, public_id: str):
    factory = request.app.state.sessionmaker
    if factory is None:
        return RedirectResponse("/", status_code=303)
    async with factory() as session:
        found = await certificate_by_public_id(session, public_id)
    if found is None:
        return RedirectResponse("/", status_code=303)
    cert, holder = found
    language_name = _language_name(cert.language) or cert.language
    image, signer_name = await _signature_file(request)
    return _pdf_response(holder.name, language_name, format_issued(cert.issued_at), cert.public_id, image, signer_name)


@router.get("/app/admin")
async def admin_home(request: Request):
    user = await _player(request)
    refused = _require_admin(user)
    if refused:
        return refused
    reports = []
    factory = request.app.state.sessionmaker
    if factory is not None:
        async with factory() as session:
            reports = await user_reports(session)
            issued = await issued_language_map(session, [person["id"] for person in reports])
    else:
        issued = {}
    for person in reports:
        person["language_name"] = _language_name(person["language"]) or "Not chosen"
        person["unlock_language"] = person["language"] or "python"
        person["issued_names"] = [_language_name(code) or code for code in issued.get(person["id"], [])]
        person["issued_codes"] = issued.get(person["id"], [])
    return TEMPLATES.TemplateResponse(
        request,
        "admin.html",
        {
            "user": user,
            "players": reports,
            "total": len(DSA_GAMES),
            "signature": await _signature_context(request),
            "signature_notice": SIGNATURE_NOTICES.get(request.query_params.get("notice") or "", ""),
        },
    )


@router.post("/app/admin/users/{user_id}/certificate")
async def grant_certificate(request: Request, user_id: int, language: str = Form("")):
    user = await _player(request)
    refused = _require_admin(user)
    if refused:
        return refused
    factory = request.app.state.sessionmaker
    if factory is not None:
        async with factory() as session:
            await issue_certificate(session, user_id, language)
    return RedirectResponse("/app/admin", status_code=303)


@router.get("/signature")
async def signature_image(request: Request):
    image, _name = await _signature_file(request)
    if not image:
        return Response(status_code=404)
    return Response(content=image, media_type="image/png")


@router.post("/app/admin/signature")
async def save_admin_signature(
    request: Request,
    signer_name: str = Form(""),
    drawn: str = Form(""),
    upload: UploadFile | None = File(None),
):
    user = await _player(request)
    refused = _require_admin(user)
    if refused:
        return refused
    factory = request.app.state.sessionmaker
    if factory is None:
        return RedirectResponse("/app/admin?notice=signature", status_code=303)
    name = signer_name.strip()
    if not name:
        name = (user or {}).get("name") or "Founder"
    raw = b""
    if upload is not None and upload.filename:
        raw = await upload.read()
    elif drawn.strip():
        try:
            raw = decode_drawn(drawn)
        except SignatureError:
            return RedirectResponse("/app/admin?notice=signature", status_code=303)
    if not raw:
        return RedirectResponse("/app/admin?notice=signature", status_code=303)
    try:
        image = normalize_signature(raw)
    except SignatureError:
        return RedirectResponse("/app/admin?notice=signature_type", status_code=303)
    async with factory() as session:
        await save_signature(session, name[:200], image)
    return RedirectResponse("/app/admin?notice=saved", status_code=303)


@router.get("/app/sql")
async def sql_track(request: Request):
    user = await _player(request)
    if not user:
        return RedirectResponse("/", status_code=303)
    return TEMPLATES.TemplateResponse(
        request,
        "sql.html",
        {"user": user, "tasks": SQL_TASKS},
    )
