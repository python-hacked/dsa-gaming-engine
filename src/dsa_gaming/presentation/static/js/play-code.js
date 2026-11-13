export async function runProgram(slug, roundId, source) {
  const response = await fetch("/api/play/" + slug + "/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ round_id: roundId, source }),
  });
  return response.json();
}

export function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
