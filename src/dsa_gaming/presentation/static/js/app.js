const clock = document.querySelector("#clock");
if (clock && clock.dataset.expires) {
  const ends = new Date(clock.dataset.expires).getTime();
  const tick = () => {
    const left = Math.max(0, ends - Date.now());
    const minutes = Math.floor(left / 60000);
    const seconds = Math.floor((left % 60000) / 1000);
    clock.textContent = minutes + ":" + String(seconds).padStart(2, "0") + " left";
  };
  tick();
  setInterval(tick, 1000);
}
