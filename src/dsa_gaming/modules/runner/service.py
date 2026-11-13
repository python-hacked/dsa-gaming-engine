import asyncio
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

import httpx

from dsa_gaming.core.config import get_settings

RUNTIMES = {
    "python": ("python", "3.10.0", "main.py"),
    "javascript": ("javascript", "18.15.0", "main.js"),
    "typescript": ("typescript", "5.0.3", "main.ts"),
    "java": ("java", "15.0.2", "Main.java"),
    "c": ("c", "10.2.0", "main.c"),
    "cpp": ("c++", "10.2.0", "main.cpp"),
    "csharp": ("csharp", "6.12.0", "Main.cs"),
    "go": ("go", "1.16.2", "main.go"),
    "rust": ("rust", "1.68.2", "main.rs"),
    "kotlin": ("kotlin", "1.8.20", "Main.kt"),
    "ruby": ("ruby", "3.0.1", "main.rb"),
    "php": ("php", "8.2.3", "main.php"),
    "swift": ("swift", "5.3.3", "main.swift"),
}


class RunError(Exception):
    def __init__(self, detail: str, stdout: str = "", stderr: str = ""):
        super().__init__(detail)
        self.detail = detail
        self.stdout = stdout
        self.stderr = stderr


def parse_trace(stdout: str) -> dict:
    for line in reversed(stdout.splitlines()):
        text = line.strip()
        if not text or text[0] not in "{[":
            continue
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            if "order" not in data and isinstance(data.get("tiles"), list) and "swaps" not in data:
                data = {**data, "order": data["tiles"]}
            if any(key in data for key in ("order", "swaps", "path", "bad", "cells")):
                return data
        elif isinstance(data, list) and data and all(_pair(item) for item in data):
            return {"path": [_pair(item) for item in data]}
        elif isinstance(data, list) and all(isinstance(item, str) for item in data):
            return {"moves": data}
        elif isinstance(data, list) and _flat_ints(data):
            return {"order": data}
    raise RunError(
        'Print the finished row as JSON, for example {"order": [1, 2, 3, 4, 5]}.',
        stdout=stdout,
    )


def _flat_ints(values: list) -> bool:
    return bool(values) and all(isinstance(item, int) and not isinstance(item, bool) for item in values)


def _pair(value) -> list[int] | None:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return None
    left, right = value
    if isinstance(left, bool) or isinstance(right, bool):
        return None
    if not isinstance(left, int) or not isinstance(right, int):
        return None
    return [left, right]


_MOVES = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1),
    "u": (-1, 0),
    "d": (1, 0),
    "l": (0, -1),
    "r": (0, 1),
    "north": (-1, 0),
    "south": (1, 0),
    "west": (0, -1),
    "east": (0, 1),
}


def interpret_output(slug: str, stdout: str) -> dict:
    trace: dict = {}
    try:
        trace = parse_trace(stdout)
    except RunError:
        trace = {}
    if slug == "graph-maze":
        path = _maze_path(stdout, trace)
        if not path:
            raise RunError(
                "Print the path to the exit. Coordinates or up, down, left, right both work.",
                stdout=stdout,
            )
        return {"path": path}
    if slug == "stack-brackets":
        bad = _bad_indexes(stdout, trace)
        if bad is None:
            raise RunError("Print the indexes of the brackets that do not match.", stdout=stdout)
        return {"bad": bad}
    if slug == "queue-flood":
        cells = _flood_cells(stdout, trace)
        if not cells:
            raise RunError("Print every open cell the flood reaches, starting at [0, 0].", stdout=stdout)
        return {"cells": cells}
    if trace:
        return trace
    order = _order_from_text(stdout)
    if order:
        return {"order": order}
    raise RunError(
        'Print the finished row as JSON, for example {"order": [1, 2, 3, 4, 5]}.',
        stdout=stdout,
    )


def _flood_cells(stdout: str, trace: dict) -> list[list[int]] | None:
    raw = trace.get("cells")
    if isinstance(raw, list) and raw and all(_pair(item) for item in raw):
        return [_pair(item) for item in raw]
    path = trace.get("path")
    if isinstance(path, list) and path and all(_pair(item) for item in path):
        return [_pair(item) for item in path]
    coords = _coordinate_lines(stdout)
    return coords or None


def _bad_indexes(stdout: str, trace: dict) -> list[int] | None:
    raw = trace.get("bad")
    if isinstance(raw, list) and all(isinstance(item, int) and not isinstance(item, bool) for item in raw):
        return list(raw)
    order = trace.get("order")
    if isinstance(order, list) and _flat_ints(order):
        return list(order)
    if stdout.strip() == "[]":
        return []
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    if lines and all(re.fullmatch(r"-?\d+", line) for line in lines):
        return [int(line) for line in lines]
    return None


def _maze_path(stdout: str, trace: dict) -> list[list[int]] | None:
    raw = trace.get("path")
    if isinstance(raw, list) and raw and all(_pair(step) for step in raw):
        return [_pair(step) for step in raw]
    moves = trace.get("moves")
    if isinstance(moves, list):
        walked = _directions_to_path([str(item) for item in moves])
        if walked:
            return walked
    coords = _coordinate_lines(stdout)
    if coords:
        if coords[0] != [0, 0]:
            coords.insert(0, [0, 0])
        return coords
    words = _direction_words(stdout)
    if words:
        return _directions_to_path(words)
    return None


def _directions_to_path(moves: list[str]) -> list[list[int]] | None:
    row, col = 0, 0
    path = [[0, 0]]
    for move in moves:
        step = _MOVES.get(move.strip().lower())
        if step is None:
            return None
        row += step[0]
        col += step[1]
        path.append([row, col])
    if len(path) < 2:
        return None
    return path


def _direction_words(text: str) -> list[str] | None:
    words = re.findall(r"[A-Za-z]+", text)
    if not words or not all(word.lower() in _MOVES for word in words):
        return None
    return [word.lower() for word in words]


def _coordinate_lines(stdout: str) -> list[list[int]]:
    found = []
    for line in stdout.splitlines():
        match = re.fullmatch(r"\s*\[?\s*(-?\d+)\s*[, ]\s*(-?\d+)\s*\]?\s*", line)
        if match:
            found.append([int(match.group(1)), int(match.group(2))])
    return found


def _order_from_text(stdout: str) -> list[int] | None:
    for line in reversed(stdout.splitlines()):
        numbers = re.findall(r"-?\d+", line)
        if len(numbers) >= 2 and not re.search(r"[A-Za-z]", line):
            return [int(number) for number in numbers]
    return None


_piston_closed = False


def _remote_runner_enabled() -> bool:
    if _piston_closed:
        return False
    settings = get_settings()
    # emkc.org stopped public execution on 15 Feb 2026. Local runs use this machine.
    if settings.app_env != "production" and "emkc.org" in settings.piston_api_url:
        return False
    return True


def sniff_language(source: str) -> str | None:
    """Use the language the program is written in when it is obvious."""
    for line in source.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "//")):
            continue
        if stripped.startswith(("const ", "let ", "var ", "function", "console.", "export ")):
            return "javascript"
        if "require(" in stripped or "=>" in stripped:
            return "javascript"
        if stripped.startswith("import ") and " from " in stripped:
            return "javascript"
        if stripped.startswith(("def ", "class ", "import ", "from ", "print(", "elif ", "lambda ")):
            return "python"
        return None
    return None


def repair_source(source: str) -> str:
    """Finish a line that stops on `else`. The real row arrives on stdin."""
    lines = source.splitlines()
    repaired = [line.rstrip() + " []" if re.search(r"\belse\s*$", line) else line for line in lines]
    if source.endswith("\n"):
        return "\n".join(repaired) + "\n"
    return "\n".join(repaired)


async def execute_source(language: str, source: str, stdin: str = "") -> tuple[str, str, int]:
    global _piston_closed
    if language not in RUNTIMES:
        raise RunError("This language is not wired to the runner yet.")
    if len(source) > 12000:
        raise RunError("That file is too long.")
    sniffed = sniff_language(source)
    if sniffed in RUNTIMES:
        language = sniffed
    if language == "python":
        source = repair_source(source)
    if _remote_runner_enabled():
        try:
            return await _piston(language, source, stdin)
        except RunError:
            raise
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (401, 403):
                _piston_closed = True
            elif get_settings().app_env == "production":
                raise RunError("The code runner is not reachable. Try again in a moment.") from None
        except Exception:
            if get_settings().app_env == "production":
                raise RunError("The code runner is not reachable. Try again in a moment.") from None
    if get_settings().app_env != "production":
        return await _local(language, source, stdin)
    raise RunError("The public code runner is closed. Host a runner and set PISTON_API_URL.")


async def _piston(language: str, source: str, stdin: str = "") -> tuple[str, str, int]:
    piston_language, version, filename = RUNTIMES[language]
    url = get_settings().piston_api_url.rstrip("/") + "/execute"
    async with httpx.AsyncClient(timeout=25) as client:
        response = await client.post(
            url,
            json={
                "language": piston_language,
                "version": version,
                "files": [{"name": filename, "content": source}],
                "stdin": stdin,
                "run_timeout": 3000,
                "compile_timeout": 10000,
            },
        )
    response.raise_for_status()
    payload = response.json()
    compiled = payload.get("compile") or {}
    ran = payload.get("run") or {}
    stdout = ran.get("stdout") or ""
    stderr = "\n".join(part for part in (compiled.get("stderr") or "", ran.get("stderr") or "") if part).strip()
    if compiled.get("code") not in (0, None):
        return stdout, stderr, int(compiled.get("code") or 1)
    code = ran.get("code")
    return stdout, stderr, 0 if code is None else int(code)


async def _local(language: str, source: str, stdin: str = "") -> tuple[str, str, int]:
    if language == "python":
        return await _local_python(source, stdin)
    if language == "javascript":
        return await _script(source, "main.js", [_command("node"), "main.js"], 3, stdin)
    if language == "typescript":
        return await _script(source, "main.ts", [_command("node"), "--experimental-strip-types", "main.ts"], 4, stdin)
    if language == "ruby":
        return await _script(source, "main.rb", [_command("ruby"), "main.rb"], 3, stdin)
    if language == "php":
        return await _script(source, "main.php", [_command("php"), "main.php"], 3, stdin)
    if language == "go":
        return await _script(source, "main.go", [_command("go"), "run", "main.go"], 8, stdin)
    if language == "c":
        return await _compile_run(source, "main.c", [_command("gcc"), "-O2", "-o", "main", "main.c"], ["./main"], stdin=stdin)
    if language == "cpp":
        return await _compile_run(source, "main.cpp", [_command("g++"), "-O2", "-o", "main", "main.cpp"], ["./main"], stdin=stdin)
    if language == "java":
        return await _compile_run(source, "Main.java", [_command("javac"), "Main.java"], [_command("java"), "-cp", ".", "Main"], stdin=stdin)
    if language == "swift":
        return await _compile_run(source, "main.swift", [_command("swiftc"), "-o", "main", "main.swift"], ["./main"], stdin=stdin, compile_timeout=20)
    if language == "rust":
        return await _compile_run(source, "main.rs", [_command("rustc"), "-O", "-o", "main", "main.rs"], ["./main"], stdin=stdin, compile_timeout=20)
    if language == "kotlin":
        return await _compile_run(source, "Main.kt", [_command("kotlinc"), "Main.kt", "-include-runtime", "-d", "main.jar"], [_command("java"), "-jar", "main.jar"], stdin=stdin, compile_timeout=20)
    raise RunError(f"{language} is not installed on this machine, and the public code runner is closed.")


def _command(name: str) -> str:
    found = shutil.which(name)
    if found:
        return found
    raise RunError(f"{name} is not installed on this machine, and the public code runner is closed.")


def _local_env(folder: str) -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", ""),
        "HOME": folder,
        "TMPDIR": folder,
        "LANG": "C.UTF-8",
        "PYTHONIOENCODING": "utf-8",
        "GOCACHE": folder,
        "GOPATH": folder,
        "GO111MODULE": "off",
    }


async def _spawn(argv: list[str], folder: str, timeout: float, stdin: str = "") -> tuple[str, str, int]:
    process = await asyncio.create_subprocess_exec(
        *argv,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=folder,
        env=_local_env(folder),
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(stdin.encode()), timeout=timeout)
    except asyncio.TimeoutError:
        process.kill()
        return "", "The program took too long.", 1
    return stdout.decode(errors="replace"), stderr.decode(errors="replace"), process.returncode or 0


async def _script(source: str, filename: str, argv: list[str], timeout: float, stdin: str = "") -> tuple[str, str, int]:
    with tempfile.TemporaryDirectory() as folder:
        (Path(folder) / filename).write_text(source, encoding="utf-8")
        return await _spawn(argv, folder, timeout, stdin)


async def _compile_run(
    source: str,
    filename: str,
    compile_argv: list[str],
    run_argv: list[str],
    compile_timeout: float = 8,
    stdin: str = "",
) -> tuple[str, str, int]:
    with tempfile.TemporaryDirectory() as folder:
        (Path(folder) / filename).write_text(source, encoding="utf-8")
        stdout, stderr, code = await _spawn(compile_argv, folder, compile_timeout)
        if code != 0:
            return stdout, stderr, code
        return await _spawn(run_argv, folder, 3, stdin)


async def _local_python(source: str, stdin: str = "") -> tuple[str, str, int]:
    with tempfile.TemporaryDirectory() as folder:
        (Path(folder) / "main.py").write_text(source, encoding="utf-8")
        return await _spawn([sys.executable, "-I", "main.py"], folder, 2, stdin)
