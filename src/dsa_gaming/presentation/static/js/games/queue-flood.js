import { runProgram, wait } from "/static/js/play-code.js";

const board = document.querySelector("#board");
const puzzle = JSON.parse(document.querySelector("#puzzle-data").textContent);
const help = document.querySelector("#help");
const result = document.querySelector("#result");
const run = document.querySelector("#run");
const source = document.querySelector("#source");
const start = puzzle.start;
const flooded = new Set([key(start[0], start[1])]);
let done = false;
let playing = false;

help.textContent = "Flood every open cell a queue can reach from the start. Any logic is fine. Print the cells, then press Run.";

function key(row, col) {
  return row + "," + col;
}

function open(row, col) {
  return puzzle.walls[row] && puzzle.walls[row][col] === false;
}

function beside(row, col) {
  return [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dRow, dCol]) => flooded.has(key(row + dRow, col + dCol)));
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
      if (flooded.has(key(rowIndex, colIndex))) cell.classList.add("is-flood");
      cell.addEventListener("click", () => choose(rowIndex, colIndex));
      grid.append(cell);
    });
  });
  board.replaceChildren(grid);
}

function cells() {
  return [...flooded].map((item) => item.split(",").map(Number));
}

function show(body) {
  result.textContent = body.passed ? "Cleared. " + body.detail : body.detail;
  if (body.passed) document.querySelector("#submit").hidden = false;
}

async function choose(row, col) {
  if (done || playing || !open(row, col) || flooded.has(key(row, col)) || !beside(row, col)) return;
  flooded.add(key(row, col));
  paint();
  const response = await fetch("/api/play/queue-flood", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ round_id: Number(board.dataset.round), cells: cells() }),
  });
  const body = await response.json();
  show(body);
  done = Boolean(body.passed);
}

async function playCells(trace) {
  flooded.clear();
  done = false;
  paint();
  for (const step of trace) {
    if (!Array.isArray(step)) continue;
    flooded.add(key(step[0], step[1]));
    paint();
    await wait(160);
  }
}

run.addEventListener("click", async () => {
  if (playing) return;
  playing = true;
  run.disabled = true;
  result.textContent = "Running…";
  const body = await runProgram("queue-flood", Number(board.dataset.round), source.value);
  if (Array.isArray(body.cells) && body.cells.length) await playCells(body.cells);
  show(body);
  done = Boolean(body.passed);
  playing = false;
  run.disabled = false;
});

paint();
