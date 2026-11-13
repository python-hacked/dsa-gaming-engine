import asyncio
import json
import os
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
            if any(key in data for key in ("order", "swaps", "path")):
                return data
        elif isinstance(data, list) and _flat_ints(data):
            return {"order": data}
    raise RunError(
        'Print the finished row as JSON, for example {"order": [1, 2, 3, 4, 5]}.',
        stdout=stdout,
    )


def _flat_ints(values: list) -> bool:
    return bool(values) and all(isinstance(item, int) and not isinstance(item, bool) for item in values)


async def execute_source(language: str, source: str) -> tuple[str, str, int]:
    if language not in RUNTIMES:
        raise RunError("This language is not wired to the runner yet.")
    if len(source) > 12000:
        raise RunError("That file is too long.")
    try:
        return await _piston(language, source)
    except RunError:
        raise
    except Exception:
        if language == "python" and get_settings().app_env != "production":
            return await _local_python(source)
        raise RunError("The code runner is not reachable. Try again in a moment.") from None


async def _piston(language: str, source: str) -> tuple[str, str, int]:
    piston_language, version, filename = RUNTIMES[language]
    url = get_settings().piston_api_url.rstrip("/") + "/execute"
    async with httpx.AsyncClient(timeout=25) as client:
        response = await client.post(
            url,
            json={
                "language": piston_language,
                "version": version,
                "files": [{"name": filename, "content": source}],
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


async def _local_python(source: str) -> tuple[str, str, int]:
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "main.py"
        path.write_text(source, encoding="utf-8")
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-I",
            str(path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=folder,
            env={"PATH": os.environ.get("PATH", ""), "PYTHONIOENCODING": "utf-8"},
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=2)
        except asyncio.TimeoutError:
            process.kill()
            return "", "The program took too long.", 1
    return stdout.decode(), stderr.decode(), process.returncode or 0
