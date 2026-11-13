import { runProgram, wait } from "/static/js/play-code.js";

const board = document.querySelector("#board");
const puzzle = JSON.parse(document.querySelector("#puzzle-data").textContent);
const help = document.querySelector("#help");
const result = document.querySelector("#result");
const run = document.querySelector("#run");
const source = document.querySelector("#source");
const brackets = puzzle.brackets.split("");
const marked = new Set();
let done = false;
let playing = false;

help.textContent = "Mark the brackets a stack cannot match. Any logic is fine. Print their indexes, then press Run.";

function paint() {
  board.replaceChildren();
  const row = document.createElement("div");
  row.className = "tiles";
  brackets.forEach((value, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "tile" + (marked.has(index) ? " is-bad" : "");
    button.textContent = value;
    button.addEventListener("click", () => choose(index));
    row.append(button);
  });
  board.append(row);
}

function show(body) {
  result.textContent = body.passed ? "Cleared. " + body.detail : body.detail;
  if (body.passed) document.querySelector("#submit").hidden = false;
}

async function choose(index) {
  if (done || playing) return;
  if (marked.has(index)) marked.delete(index);
  else marked.add(index);
  paint();
  const response = await fetch("/api/play/stack-brackets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ round_id: Number(board.dataset.round), bad: [...marked] }),
  });
  const body = await response.json();
  show(body);
  done = Boolean(body.passed);
}

async function playBad(indexes) {
  marked.clear();
  done = false;
  paint();
  for (const index of indexes) {
    marked.add(index);
    paint();
    await wait(220);
  }
}

run.addEventListener("click", async () => {
  if (playing) return;
  playing = true;
  run.disabled = true;
  result.textContent = "Running…";
  const body = await runProgram("stack-brackets", Number(board.dataset.round), source.value);
  if (Array.isArray(body.bad)) await playBad(body.bad);
  show(body);
  done = Boolean(body.passed);
  playing = false;
  run.disabled = false;
});

paint();
