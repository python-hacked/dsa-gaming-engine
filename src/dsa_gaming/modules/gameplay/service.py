import random
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta

MARATHON_SECONDS = 120 * 60
PLAYABLE = {"array-swap", "graph-maze"}
_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


@dataclass(frozen=True)
class Grade:
    passed: bool
    score: int
    detail: str


def deadline(started_at: datetime) -> datetime:
    return started_at + timedelta(seconds=MARATHON_SECONDS)


def clock_label(expires_at: datetime, now: datetime) -> str:
    seconds = int((expires_at - now).total_seconds())
    if seconds < 0:
        seconds = 0
    return f"{seconds // 60}:{seconds % 60:02d}"


def _ints(pair) -> tuple[int, int] | None:
    if not isinstance(pair, (list, tuple)) or len(pair) != 2:
        return None
    if not all(isinstance(number, int) and not isinstance(number, bool) for number in pair):
        return None
    return pair[0], pair[1]


def new_array(rng: random.Random | None = None) -> dict:
    rng = rng or random.Random()
    solved = [1, 2, 3, 4, 5]
    limit = 6
    for _ in range(20):
        tiles = solved[:]
        for _step in range(limit):
            index = rng.randrange(len(tiles) - 1)
            tiles[index], tiles[index + 1] = tiles[index + 1], tiles[index]
        if tiles != solved:
            return {"tiles": tiles, "swap_limit": limit}
    return {"tiles": [2, 1, 3, 5, 4], "swap_limit": limit}


def grade_array(tiles: list[int], swaps: list, swap_limit: int) -> Grade:
    if not isinstance(swaps, list) or len(swaps) > swap_limit:
        return Grade(False, 0, "Too many swaps.")
    state = list(tiles)
    for pair in swaps:
        parsed = _ints(pair)
        if parsed is None:
            return Grade(False, 0, "Those moves are not valid.")
        left, right = parsed
        if abs(left - right) != 1 or not 0 <= left < len(state) or not 0 <= right < len(state):
            return Grade(False, 0, "Swap two tiles that sit next to each other.")
        state[left], state[right] = state[right], state[left]
    if state != sorted(tiles):
        return Grade(False, 0, "The row is not sorted yet.")
    return Grade(True, 100, f"Sorted in {len(swaps)} swaps.")


def _number_row(values) -> list[int] | None:
    if not isinstance(values, list) or not values:
        return None
    row: list[int] = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, int):
            return None
        row.append(value)
    return row


def grade_array_order(tiles: list[int], order: list[int]) -> Grade:
    if len(order) != len(tiles):
        return Grade(False, 0, "Print every number in the row.")
    if sorted(order) != sorted(tiles):
        return Grade(False, 0, "Use the numbers from this row.")
    if order != sorted(tiles):
        return Grade(False, 0, "The row is not sorted yet.")
    return Grade(True, 100, "Sorted.")


def answer_from_code(tiles: list[int], trace: dict) -> tuple[Grade, list[int]]:
    """Grade a program by the row it produces. The algorithm is not checked."""
    if isinstance(trace.get("order"), list):
        order = _number_row(trace["order"])
        if order is None:
            return Grade(False, 0, "Print the finished row as numbers."), list(tiles)
        return grade_array_order(tiles, order), order
    swaps = trace.get("swaps")
    if not isinstance(swaps, list):
        return Grade(False, 0, "Print the finished row."), list(tiles)
    state = list(tiles)
    for pair in swaps:
        parsed = _ints(pair)
        if parsed is None:
            return Grade(False, 0, "Those moves are not valid."), state
        left, right = parsed
        if not (0 <= left < len(state) and 0 <= right < len(state)):
            return Grade(False, 0, "Those moves are not valid."), state
        state[left], state[right] = state[right], state[left]
    return grade_array_order(tiles, state), state


def shortest_path(walls: list[list[bool]], start: tuple[int, int], goal: tuple[int, int]) -> int | None:
    queue: deque[tuple[int, int]] = deque([start])
    distance = {start: 0}
    rows, cols = len(walls), len(walls[0])
    while queue:
        row, col = queue.popleft()
        if (row, col) == goal:
            return distance[(row, col)]
        for d_row, d_col in _DIRS:
            next_row, next_col = row + d_row, col + d_col
            step = (next_row, next_col)
            if step in distance or not (0 <= next_row < rows and 0 <= next_col < cols):
                continue
            if walls[next_row][next_col]:
                continue
            distance[step] = distance[(row, col)] + 1
            queue.append(step)
    return None


def new_maze(rng: random.Random | None = None) -> dict:
    rng = rng or random.Random()
    size = 7
    walls = [[True] * size for _ in range(size)]

    def carve(row: int, col: int) -> None:
        walls[row][col] = False
        directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]
        rng.shuffle(directions)
        for d_row, d_col in directions:
            next_row, next_col = row + d_row, col + d_col
            if 0 <= next_row < size and 0 <= next_col < size and walls[next_row][next_col]:
                walls[row + d_row // 2][col + d_col // 2] = False
                carve(next_row, next_col)

    carve(0, 0)
    optimal = shortest_path(walls, (0, 0), (size - 1, size - 1))
    if optimal is None:
        return new_maze(rng)
    return {"walls": walls, "start": [0, 0], "goal": [size - 1, size - 1], "optimal": optimal}


def grade_maze(walls: list[list[bool]], path: list, optimal: int) -> Grade:
    if not isinstance(path, list) or len(path) < 2 or len(path) > 80:
        return Grade(False, 0, "That path does not reach the exit.")
    rows, cols = len(walls), len(walls[0])
    parsed: list[tuple[int, int]] = []
    for step in path:
        cell = _ints(step)
        if cell is None:
            return Grade(False, 0, "That path is not valid.")
        row, col = cell
        if not (0 <= row < rows and 0 <= col < cols) or walls[row][col]:
            return Grade(False, 0, "The path goes through a wall.")
        parsed.append((row, col))
    if parsed[0] != (0, 0) or parsed[-1] != (rows - 1, cols - 1):
        return Grade(False, 0, "Start at the open corner and finish at the exit.")
    for (row, col), (next_row, next_col) in zip(parsed, parsed[1:]):
        if abs(row - next_row) + abs(col - next_col) != 1:
            return Grade(False, 0, "Move one open cell at a time.")
    steps = len(parsed) - 1
    extra = max(0, steps - optimal)
    score = max(50, 100 - extra * 8)
    if extra == 0:
        detail = f"Shortest path, {steps} steps."
    else:
        detail = f"Exit in {steps} steps. Shortest is {optimal}."
    return Grade(True, score, detail)


def public_payload(payload: dict) -> dict:
    shown = dict(payload)
    shown.pop("optimal", None)
    return shown


def new_puzzle(slug: str, rng: random.Random | None = None) -> dict:
    if slug == "array-swap":
        return new_array(rng)
    if slug == "graph-maze":
        return new_maze(rng)
    raise KeyError(slug)


def grade(slug: str, payload: dict, body: dict) -> Grade:
    if slug == "array-swap":
        return grade_array(payload["tiles"], body.get("swaps", []), payload["swap_limit"])
    if slug == "graph-maze":
        return grade_maze(payload["walls"], body.get("path", []), payload["optimal"])
    return Grade(False, 0, "This game is not open yet.")
