from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from dsa_gaming.modules.catalog.data import DSA_GAMES, editor_language
from dsa_gaming.modules.coach.repository import performance_line, recent_messages
from dsa_gaming.modules.coach.service import coach_reply
from dsa_gaming.modules.gameplay.repository import active_run, get_round, use_language
from dsa_gaming.modules.gameplay.service import PLAYABLE
from dsa_gaming.modules.identity.service import remember_google_user

router = APIRouter(prefix="/api/coach", tags=["coach"])


def _title(slug: str) -> str:
    for game in DSA_GAMES:
        if game["slug"] == slug:
            return game["title"]
    return slug


@router.get("/{slug}")
async def coach_history(slug: str, request: Request):
    user = request.session.get("user")
    if not user:
        return JSONResponse({"detail": "Sign in first."}, status_code=401)
    factory = request.app.state.sessionmaker
    if factory is None:
        return JSONResponse({"detail": "Database is not ready."}, status_code=503)
    user = await remember_google_user(request, user)
    async with factory() as session:
        stats = await performance_line(session, int(user["id"]), slug)
        rows = await recent_messages(session, int(user["id"]), slug)
    return {
        "performance": stats,
        "messages": [{"role": row.role, "content": row.content} for row in rows],
    }


@router.post("/{slug}")
async def coach_ask(slug: str, request: Request):
    user = request.session.get("user")
    if not user:
        return JSONResponse({"detail": "Sign in first."}, status_code=401)
    if slug not in PLAYABLE:
        return JSONResponse({"detail": "This game is not open yet."}, status_code=404)
    factory = request.app.state.sessionmaker
    if factory is None:
        return JSONResponse({"detail": "Database is not ready."}, status_code=503)
    api_key = request.app.state.settings.gemini_api_key.strip()
    if not api_key:
        return JSONResponse({"detail": "The assistant needs a Gemini key."}, status_code=503)
    body = await request.json()
    message = body.get("message")
    source = body.get("source") if isinstance(body.get("source"), str) else ""
    round_id = body.get("round_id")
    if not isinstance(message, str) or not message.strip() or not isinstance(round_id, int):
        return JSONResponse({"detail": "Ask a question about this task."}, status_code=400)

    user = await remember_google_user(request, user)
    async with factory() as session:
        run = await active_run(session, user["id"])
        if run is None:
            return JSONResponse({"detail": "The marathon clock has run out."}, status_code=403)
        puzzle = await get_round(session, round_id, run.id)
        if puzzle is None or puzzle.slug != slug:
            return JSONResponse({"detail": "This round is closed."}, status_code=404)
        language = await use_language(session, run, editor_language(user.get("active_language"), run.language))
        try:
            return await coach_reply(
                session,
                api_key=api_key,
                user_id=int(user["id"]),
                slug=slug,
                task=_title(slug),
                language=language,
                message=message.strip()[:2000],
                source=source,
                payload=puzzle.payload,
            )
        except Exception:
            return JSONResponse({"detail": "The assistant could not answer. Try again."}, status_code=502)
