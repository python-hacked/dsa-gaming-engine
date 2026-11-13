import { runProgram, wait } from "/static/js/play-code.js";

const board = document.querySelector("#board");
const puzzle = JSON.parse(document.querySelector("#puzzle-data").textContent);
const help = document.querySelector("#help");
const result = document.querySelector("#result");
const run = document.querySelector("#run");
const source = document.querySelector("#source");
const start = puzzle.start;
const goal = puzzle.goal;
let player = start.slice();
let path = [start.slice()];
let done = false;
let playing = false;

help.textContent = "Reach the exit with any logic, then press Run. The token follows the path your program prints.";

function open(row, col) {
  return puzzle.walls[row] && puzzle.walls[row][col] === false;
}

function paint() {
  const grid = document.createElement("div");
  grid.className = "maze";
  grid.style.setProperty("--cols", String(puzzle.walls[0].length));
  puzzle.walls.forEach((row, rowIndex) => {
    row.forEach((wall, colIndex) => {
      const cell = document.createElement("button");
      cell.type = "button";
      cell.className = "cell" + (wall ? " is-wall" : "");
      if (rowIndex === player[0] && colIndex === player[1]) cell.classList.add("is-player");
      if (rowIndex === goal[0] && colIndex === goal[1]) cell.classList.add("is-goal");
      if (path.some((step) => step[0] === rowIndex && step[1] === colIndex)) cell.classList.add("is-path");
      cell.addEventListener("click", () => move(rowIndex, colIndex));
      grid.append(cell);
    });
  });
  board.replaceChildren(grid);
}

function show(body) {
  result.textContent = body.passed ? "Cleared. " + body.detail + " Score " + body.score + "." : body.detail;
  if (body.passed) document.querySelector("#submit").hidden = false;
}

async function finish() {
  done = true;
  const response = await fetch("/api/play/graph-maze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ round_id: Number(board.dataset.round), path }),
  });
  show(await response.json());
}

function move(row, col) {
  if (done || playing || !open(row, col)) return;
  if (Math.abs(player[0] - row) + Math.abs(player[1] - col) !== 1) return;
  player = [row, col];
  path.push(player.slice());
  paint();
  if (row === goal[0] && col === goal[1]) finish();
}

async function playPath(trace) {
  player = start.slice();
  path = [start.slice()];
  done = false;
  paint();
  for (const step of trace.slice(1)) {
    if (!Array.isArray(step)) continue;
    player = [step[0], step[1]];
    path.push(player.slice());
    paint();
    await wait(180);
  }
}

document.addEventListener("keydown", (event) => {
  const steps = { ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] };
  const step = steps[event.key];
  if (!step || event.target === source) return;
  event.preventDefault();
  move(player[0] + step[0], player[1] + step[1]);
});

run.addEventListener("click", async () => {
  if (playing) return;
  playing = true;
  run.disabled = true;
  result.textContent = "Running…";
  const body = await runProgram("graph-maze", Number(board.dataset.round), source.value);
  if (Array.isArray(body.path) && body.path.length) await playPath(body.path);
  show(body);
  done = Boolean(body.passed);
  playing = false;
  run.disabled = false;
});

paint();
