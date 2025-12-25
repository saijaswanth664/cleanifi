// UI interactions only (NO backend calls)

document.addEventListener("DOMContentLoaded", () => {
  const buttons = document.querySelectorAll(".btn");

  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      btn.classList.add("pressed");
      setTimeout(() => btn.classList.remove("pressed"), 150);
    });
  });
});
