from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from dsa_gaming.modules.gameplay.repository import active_run, get_round, save_attempt
from dsa_gaming.modules.gameplay.service import PLAYABLE, answer_from_code, grade
from dsa_gaming.modules.identity.service import remember_google_user
from dsa_gaming.modules.runner.service import RunError, execute_source, parse_trace

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
        moves = body.get("swaps") if slug == "array-swap" else body.get("path")
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
            return {"passed": True, "score": 100, "detail": "Already cleared.", "swaps": [], "path": []}
        try:
            stdout, stderr, _code = await execute_source(run.language, source)
        except RunError as exc:
            return {
                "passed": False,
                "score": 0,
                "detail": exc.stderr or exc.detail,
                "stdout": exc.stdout,
                "stderr": exc.stderr,
                "swaps": [],
                "path": [],
            }
        try:
            trace = parse_trace(stdout)
        except RunError as exc:
            return {
                "passed": False,
                "score": 0,
                "detail": stderr or exc.detail,
                "stdout": stdout,
                "stderr": stderr,
                "swaps": [],
                "path": [],
            }
        if slug == "array-swap":
            result, order = answer_from_code(puzzle.payload["tiles"], trace)
            moves = order
            swaps = trace.get("swaps") if isinstance(trace.get("swaps"), list) else []
            path: list = []
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
                }
            result = grade(slug, puzzle.payload, trace)
            moves = path
            swaps = []
            order = []
        await save_attempt(session, puzzle, moves, result.score, result.passed)
    return {
        "passed": result.passed,
        "score": result.score,
        "detail": result.detail,
        "order": order,
        "swaps": swaps,
        "path": path,
        "stdout": stdout,
        "stderr": stderr,
    }
