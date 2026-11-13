const pad = document.querySelector("#sign-pad");
const form = document.querySelector("#sign-draw-form");
if (pad && form) {
  const ctx = pad.getContext("2d");
  let drawing = false;
  let dirty = false;

  function point(event) {
    const box = pad.getBoundingClientRect();
    return {
      x: ((event.clientX - box.left) / box.width) * pad.width,
      y: ((event.clientY - box.top) / box.height) * pad.height,
    };
  }

  function start(event) {
    drawing = true;
    const at = point(event);
    ctx.strokeStyle = "#12306b";
    ctx.lineWidth = 5;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(at.x, at.y);
  }

  function move(event) {
    if (!drawing) return;
    const at = point(event);
    ctx.lineTo(at.x, at.y);
    ctx.stroke();
    dirty = true;
  }

  pad.addEventListener("pointerdown", (event) => {
    pad.setPointerCapture(event.pointerId);
    start(event);
  });
  pad.addEventListener("pointermove", move);
  pad.addEventListener("pointerup", () => {
    drawing = false;
  });
  pad.addEventListener("pointerleave", () => {
    drawing = false;
  });

  document.querySelector("#sign-clear")?.addEventListener("click", () => {
    ctx.clearRect(0, 0, pad.width, pad.height);
    dirty = false;
  });

  form.addEventListener("submit", (event) => {
    if (!dirty) {
      event.preventDefault();
      return;
    }
    document.querySelector("#sign-drawn").value = pad.toDataURL("image/png");
  });
}
