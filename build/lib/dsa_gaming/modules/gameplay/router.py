from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from dsa_gaming.modules.catalog.data import editor_language
from dsa_gaming.modules.gameplay.repository import active_run, get_round, save_attempt, use_language
from dsa_gaming.modules.gameplay.service import PLAYABLE, answer_from_code, grade, program_input
from dsa_gaming.modules.identity.service import remember_google_user
from dsa_gaming.modules.runner.service import RunError, execute_source, interpret_output

router = APIRouter(prefix="/api/play", tags=["gameplay"])


@router.post("/{slug}")
async def submit_play(slug: str, request: Request):
    user = request.session.get("user")
    if not user:
        return JSONResponse({"passed": False, "detail": "Sign in first."}, status_code=401)
    if slug not in PLAYABLE:
        return JSONResponse({"passed": False, "detail": "This game is not open yet."}, status_code=404)
    factory = request.app.state.sessionmaker
    if factory is None:
        return JSONResponse({"passed": False, "detail": "Database is not ready."}, status_code=503)
    body = await request.json()
    round_id = body.get("round_id")
    if not isinstance(round_id, int):
        return JSONResponse({"passed": False, "detail": "Missing round."}, status_code=400)

    user = await remember_google_user(request, user)
    async with factory() as session:
        run = await active_run(session, user["id"])
        if run is None:
            return JSONResponse({"passed": False, "detail": "The marathon clock has run out."}, status_code=403)
        puzzle = await get_round(session, round_id, run.id)
        if puzzle is None or puzzle.slug != slug:
            return JSONResponse({"passed": False, "detail": "This round is closed."}, status_code=404)
        if puzzle.status == "passed":
            return {"passed": True, "score": 100, "detail": "Already cleared."}
        result = grade(slug, puzzle.payload, body)
        if slug == "array-swap":
            moves = body.get("swaps")
        elif slug == "stack-brackets":
            moves = body.get("bad")
        elif slug == "queue-flood":
            moves = body.get("cells")
        else:
            moves = body.get("path")
        if result.passed or puzzle.status == "open":
            await save_attempt(session, puzzle, moves if isinstance(moves, list) else [], result.score, result.passed)
    return {"passed": result.passed, "score": result.score, "detail": result.detail}


@router.post("/{slug}/run")
async def run_code(slug: str, request: Request):
    user = request.session.get("user")
    if not user:
        return JSONResponse({"passed": False, "detail": "Sign in first."}, status_code=401)
    if slug not in PLAYABLE:
        return JSONResponse({"passed": False, "detail": "This game is not open yet."}, status_code=404)
    factory = request.app.state.sessionmaker
    if factory is None:
        return JSONResponse({"passed": False, "detail": "Database is not ready."}, status_code=503)
    body = await request.json()
    round_id = body.get("round_id")
    source = body.get("source")
    if not isinstance(round_id, int) or not isinstance(source, str):
        return JSONResponse({"passed": False, "detail": "Missing the program."}, status_code=400)

    user = await remember_google_user(request, user)
    async with factory() as session:
        run = await active_run(session, user["id"])
        if run is None:
            return JSONResponse({"passed": False, "detail": "The marathon clock has run out."}, status_code=403)
        puzzle = await get_round(session, round_id, run.id)
        if puzzle is None or puzzle.slug != slug:
            return JSONResponse({"passed": False, "detail": "This round is closed."}, status_code=404)
        if puzzle.status == "passed":
            return {"passed": True, "score": 100, "detail": "Already cleared.", "order": [], "swaps": [], "path": [], "bad": []}
        language = await use_language(session, run, editor_language(user.get("active_language"), run.language))
        try:
            stdout, stderr, _code = await execute_source(language, source, program_input(slug, puzzle.payload))
        except RunError as exc:
            return {
                "passed": False,
                "score": 0,
                "detail": exc.stderr or exc.detail,
                "stdout": exc.stdout,
                "stderr": exc.stderr,
                "order": [],
                "swaps": [],
                "path": [],
                "bad": [],
            }
        try:
            trace = interpret_output(slug, stdout)
        except RunError as exc:
            detail = stderr.strip() or exc.detail
            if stdout.strip() and not stderr.strip():
                detail = exc.detail + " Program printed: " + stdout.strip()[:300]
            return {
                "passed": False,
                "score": 0,
                "detail": detail,
                "stdout": stdout,
                "stderr": stderr,
                "order": [],
                "swaps": [],
                "path": [],
                "bad": [],
            }
        order: list = []
        swaps: list = []
        path: list = []
        bad: list = []
        cells: list = []
        if slug == "array-swap":
            result, order = answer_from_code(puzzle.payload["tiles"], trace)
            moves = order
            swaps = trace.get("swaps") if isinstance(trace.get("swaps"), list) else []
        elif slug == "stack-brackets":
            bad = trace.get("bad") if isinstance(trace.get("bad"), list) else []
            result = grade(slug, puzzle.payload, {"bad": bad})
            moves = bad
        elif slug == "queue-flood":
            cells = trace.get("cells") if isinstance(trace.get("cells"), list) else []
            result = grade(slug, puzzle.payload, {"cells": cells})
            moves = cells
        else:
            path = trace.get("path") if isinstance(trace.get("path"), list) else []
            if not path:
                return {
                    "passed": False,
                    "score": 0,
                    "detail": "Print the path that reaches the exit.",
                    "stdout": stdout,
                    "stderr": stderr,
                    "order": [],
                    "swaps": [],
                    "path": [],
                    "bad": [],
                }
            result = grade(slug, puzzle.payload, trace)
            moves = path
        await save_attempt(session, puzzle, moves, result.score, result.passed)
    return {
        "passed": result.passed,
        "score": result.score,
        "detail": result.detail,
        "order": order,
        "swaps": swaps,
        "path": path,
        "bad": bad,
        "cells": cells,
        "stdout": stdout,
        "stderr": stderr,
    }
