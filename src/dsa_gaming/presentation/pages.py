import json
from pathlib import Path

from fastapi import APIRouter, Form, Request
from markupsafe import Markup
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from dsa_gaming.modules.catalog.data import DSA_GAMES, LANGUAGE_IDS, LANGUAGES, SQL_TASKS
from dsa_gaming.modules.gameplay.repository import active_run, begin_round, cleared_slugs, start_run
from dsa_gaming.modules.gameplay.service import PLAYABLE, clock_label, public_payload
from dsa_gaming.modules.identity.models import utcnow
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
}


def _language_name(code: str | None) -> str:
    for language_id, name in LANGUAGES:
        if language_id == code:
            return name
    return ""


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
    if slug not in PLAYABLE:
        return RedirectResponse("/app/dsa", status_code=303)
    factory = request.app.state.sessionmaker
    if factory is None or not user.get("id"):
        return RedirectResponse("/app/dsa?notice=database", status_code=303)
    async with factory() as session:
        run = await active_run(session, user["id"])
        if run is None:
            return RedirectResponse("/app/dsa", status_code=303)
        puzzle = await begin_round(session, run.id, slug, fresh=bool(new))
        round_id = puzzle.id
        shown = public_payload(puzzle.payload)
        expires_at = run.expires_at
        language = run.language
    title = next(game["title"] for game in DSA_GAMES if game["slug"] == slug)
    return TEMPLATES.TemplateResponse(
        request,
        "play.html",
        {
            "user": user,
            "slug": slug,
            "title": title,
            "round_id": round_id,
            "puzzle_json": Markup(json.dumps(shown)),
            "starter": build_starter(slug, language, shown),
            "language_name": _language_name(language),
            "expires_at": expires_at.isoformat(),
            "label": clock_label(expires_at, utcnow()),
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
