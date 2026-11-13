import json
import re
from base64 import b64encode

import itsdangerous
import pytest
from fastapi.testclient import TestClient

from dsa_gaming.core.config import get_settings
from dsa_gaming.main import create_app
from dsa_gaming.modules.gameplay.service import (
    answer_from_code,
    grade_array,
    grade_array_order,
    grade_maze,
    new_array,
    new_maze,
    shortest_path,
)
from dsa_gaming.modules.runner.service import parse_trace
from dsa_gaming.modules.runner.starters import build_starter


def test_adjacent_swaps_that_sort_pass():
    result = grade_array([2, 1, 3, 4, 5], [[0, 1]], 6)
    assert result.passed
    assert result.score == 100


def test_jump_swap_is_rejected():
    result = grade_array([3, 1, 2, 4, 5], [[0, 2]], 6)
    assert not result.passed


def test_generated_array_is_solvable_within_the_limit():
    puzzle = new_array()
    tiles = puzzle["tiles"][:]
    swaps = []
    while tiles != sorted(tiles):
        for index in range(len(tiles) - 1):
            if tiles[index] > tiles[index + 1]:
                tiles[index], tiles[index + 1] = tiles[index + 1], tiles[index]
                swaps.append([index, index + 1])
                break
    result = grade_array(puzzle["tiles"], swaps, puzzle["swap_limit"])
    assert result.passed


def test_maze_rejects_a_wall_and_accepts_a_real_path():
    puzzle = new_maze()
    walls = puzzle["walls"]
    assert grade_maze(walls, [[0, 0], [0, 1]], puzzle["optimal"]).passed is False
    path = _bfs(walls)
    result = grade_maze(walls, path, puzzle["optimal"])
    assert result.passed
    assert result.score == 100


def _bfs(walls):
    start = (0, 0)
    goal = (len(walls) - 1, len(walls[0]) - 1)
    queue = [start]
    previous = {start: None}
    while queue:
        row, col = queue.pop(0)
        if (row, col) == goal:
            break
        for d_row, d_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            step = (row + d_row, col + d_col)
            if step in previous:
                continue
            if not (0 <= step[0] < len(walls) and 0 <= step[1] < len(walls[0])):
                continue
            if walls[step[0]][step[1]]:
                continue
            previous[step] = (row, col)
            queue.append(step)
    path = []
    cursor = goal
    while cursor is not None:
        path.append([cursor[0], cursor[1]])
        cursor = previous[cursor]
    path.reverse()
    return path


def test_shortest_helper_matches_open_row():
    walls = [[False, False, False], [True, True, True], [True, True, True]]
    assert shortest_path(walls, (0, 0), (0, 2)) == 2


def _login(client: TestClient) -> None:
    signer = itsdangerous.TimestampSigner(get_settings().session_secret)
    payload = {"user": {"sub": "play-sub", "email": "play@example.com", "name": "Player", "picture": ""}}
    raw = b64encode(json.dumps(payload).encode("utf-8"))
    client.cookies.set("dsa_session", signer.sign(raw).decode("utf-8"))


def _puzzle(html: str) -> dict:
    match = re.search(r'id="puzzle-data"[^>]*>(.*?)</script>', html)
    assert match
    return json.loads(match.group(1))


def test_array_and_maze_can_be_cleared_in_a_marathon():
    app = create_app()
    with TestClient(app) as client:
        if app.state.sessionmaker is None:
            pytest.skip("database is not configured")
        _login(client)
        client.post("/app/dsa/language", data={"language": "python"})
        client.post("/app/dsa/marathon", follow_redirects=False)
        array_page = client.get("/play/array-swap")
        array = _puzzle(array_page.text)
        round_id = int(re.search(r'data-round="(\d+)"', array_page.text).group(1))
        tiles = array["tiles"][:]
        swaps = []
        while tiles != sorted(tiles):
            for index in range(len(tiles) - 1):
                if tiles[index] > tiles[index + 1]:
                    tiles[index], tiles[index + 1] = tiles[index + 1], tiles[index]
                    swaps.append([index, index + 1])
                    break
        cleared = client.post("/api/play/array-swap", json={"round_id": round_id, "swaps": swaps})
        assert cleared.json()["passed"] is True

        maze_page = client.get("/play/graph-maze")
        maze = _puzzle(maze_page.text)
        maze_round = int(re.search(r'data-round="(\d+)"', maze_page.text).group(1))
        assert "optimal" not in maze
        path = _bfs(maze["walls"])
        maze_result = client.post("/api/play/graph-maze", json={"round_id": maze_round, "path": path})
        assert maze_result.json()["passed"] is True
        assert maze_result.json()["score"] == 100


def test_starter_uses_the_current_row():
    source = build_starter("array-swap", "python", {"tiles": [4, 2, 5, 1, 3], "swap_limit": 6})
    assert "[4, 2, 5, 1, 3]" in source
    assert '"order"' in source


def test_any_sorted_row_clears_the_code_run():
    tiles = [2, 1, 5, 4, 3]
    passed, order = answer_from_code(tiles, {"order": [1, 2, 3, 4, 5]})
    assert passed.passed
    assert order == [1, 2, 3, 4, 5]
    unsorted, shown = answer_from_code(tiles, {"order": [2, 1, 5, 4, 3]})
    assert unsorted.passed is False
    assert shown == [2, 1, 5, 4, 3]
    wrong, _shown = answer_from_code(tiles, {"order": [9, 9, 9, 9, 9]})
    assert wrong.passed is False
    jumped, jumped_row = answer_from_code(tiles, {"swaps": [[0, 4], [1, 3]]})
    assert jumped_row == [3, 4, 5, 1, 2]
    assert grade_array_order(tiles, [1, 2, 3, 4, 5]).passed


def test_parse_trace_reads_the_last_json_line():
    trace = parse_trace('working\n{"swaps": [[1, 2]]}\n')
    assert trace["swaps"] == [[1, 2]]
    assert parse_trace('debug\n[1, 2, 3, 4, 5]\n')["order"] == [1, 2, 3, 4, 5]


def test_running_code_moves_the_board(monkeypatch):
    app = create_app()
    with TestClient(app) as client:
        if app.state.sessionmaker is None:
            pytest.skip("database is not configured")
        _login(client)
        client.post("/app/dsa/language", data={"language": "python"})
        client.post("/app/dsa/marathon", follow_redirects=False)
        page = client.get("/play/array-swap?new=1")
        puzzle = _puzzle(page.text)
        round_id = int(re.search(r'data-round="(\d+)"', page.text).group(1))

        async def fake_execute(_language, _source):
            return json.dumps({"order": sorted(puzzle["tiles"])}) + "\n", "", 0

        monkeypatch.setattr("dsa_gaming.modules.gameplay.router.execute_source", fake_execute)
        response = client.post("/api/play/array-swap/run", json={"round_id": round_id, "source": "program"})
        body = response.json()
        assert body["passed"] is True
        assert body["order"] == sorted(puzzle["tiles"])
