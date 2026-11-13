import { runProgram, wait } from "/static/js/play-code.js";

const board = document.querySelector("#board");
const puzzle = JSON.parse(document.querySelector("#puzzle-data").textContent);
const help = document.querySelector("#help");
const result = document.querySelector("#result");
const run = document.querySelector("#run");
const source = document.querySelector("#source");
const startTiles = puzzle.tiles.slice();
let tiles = startTiles.slice();
let swaps = [];
let selected = null;
let done = false;
let playing = false;

help.textContent = "Sort the row with any logic in " + (document.querySelector(".editor-bar span")?.textContent || "code") + ", then press Run. The tiles change to the row your program prints.";

function paint() {
  board.replaceChildren();
  const row = document.createElement("div");
  row.className = "tiles";
  tiles.forEach((value, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "tile" + (selected === index ? " is-on" : "");
    button.textContent = String(value);
    button.addEventListener("click", () => choose(index));
    row.append(button);
  });
  board.append(row);
}

function sorted() {
  return tiles.every((value, index) => value === index + 1);
}

function show(body) {
  result.textContent = body.passed ? "Cleared. " + body.detail : body.detail;
}

async function finish() {
  done = true;
  const response = await fetch("/api/play/array-swap", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ round_id: Number(board.dataset.round), swaps }),
  });
  show(await response.json());
}

function choose(index) {
  if (done || playing) return;
  if (selected === null) {
    selected = index;
    paint();
    return;
  }
  if (Math.abs(selected - index) === 1 && swaps.length < puzzle.swap_limit) {
    const next = tiles.slice();
    next[selected] = tiles[index];
    next[index] = tiles[selected];
    tiles = next;
    swaps.push([selected, index]);
  }
  selected = null;
  paint();
  if (sorted()) finish();
  else if (swaps.length >= puzzle.swap_limit) {
    done = true;
    result.textContent = "Out of swaps. Change the code, or start a new puzzle.";
  }
}

async function playOrder(order) {
  tiles = startTiles.slice();
  selected = null;
  done = false;
  const sameNumbers = order.slice().sort((a, b) => a - b).join() === startTiles.slice().sort((a, b) => a - b).join();
  if (!sameNumbers) {
    tiles = order.slice();
    paint();
    return;
  }
  paint();
  for (let index = 0; index < order.length; index += 1) {
    if (tiles[index] === order[index]) continue;
    const from = tiles.indexOf(order[index]);
    if (from < 0) break;
    const next = tiles.slice();
    next[index] = tiles[from];
    next[from] = tiles[index];
    tiles = next;
    paint();
    await wait(220);
  }
}

run.addEventListener("click", async () => {
  if (playing) return;
  playing = true;
  run.disabled = true;
  result.textContent = "Running…";
  const body = await runProgram("array-swap", Number(board.dataset.round), source.value);
  if (Array.isArray(body.order) && body.order.length) await playOrder(body.order);
  else {
    tiles = startTiles.slice();
    paint();
  }
  show(body);
  done = Boolean(body.passed);
  playing = false;
  run.disabled = false;
});

paint();
