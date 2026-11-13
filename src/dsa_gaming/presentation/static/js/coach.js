const panel = document.querySelector(".coach");
const tab = document.querySelector("#coach-open");
const backdrop = document.querySelector(".coach-backdrop");
const log = document.querySelector("#coach-log");
const stats = document.querySelector("#coach-performance");
const form = document.querySelector("#coach-form");

function setOpen(open) {
  panel.classList.toggle("is-open", open);
  panel.setAttribute("aria-hidden", open ? "false" : "true");
  tab.setAttribute("aria-expanded", open ? "true" : "false");
  backdrop.hidden = !open;
}

function bubble(role, content) {
  const item = document.createElement("p");
  item.className = role === "player" ? "coach-bubble user" : "coach-bubble";
  item.textContent = content;
  log.append(item);
  log.scrollTop = log.scrollHeight;
  return item;
}

async function loadHistory() {
  const response = await fetch(`/api/coach/${panel.dataset.slug}`);
  if (!response.ok) return;
  const body = await response.json();
  stats.textContent = body.performance || "";
  log.replaceChildren();
  for (const message of body.messages || []) bubble(message.role, message.content);
}

if (panel && form && tab && backdrop) {
  loadHistory();
  tab.addEventListener("click", () => setOpen(!panel.classList.contains("is-open")));
  backdrop.addEventListener("click", () => setOpen(false));
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const field = form.querySelector("textarea");
    const message = field.value.trim();
    if (!message) return;
    bubble("player", message);
    field.value = "";
    const pending = bubble("assistant", "Thinking...");
    try {
      const response = await fetch(`/api/coach/${panel.dataset.slug}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          round_id: Number(panel.dataset.round),
          source: document.querySelector("#source")?.value || "",
        }),
      });
      const body = await response.json();
      if (!response.ok) {
        pending.textContent = body.detail || "The assistant could not answer.";
        return;
      }
      stats.textContent = body.performance || "";
      pending.textContent = body.reply;
    } catch (_error) {
      pending.textContent = "The assistant could not answer. Try again.";
    }
  });
}
