document.querySelectorAll("[data-loading-form]").forEach((form) => {
  form.addEventListener("submit", () => {
    const button = form.querySelector('button[type="submit"]');
    const note = form.querySelector(".loading-note");
    if (button) button.disabled = true;
    if (note) note.classList.add("is-visible");
  });
});

document.querySelectorAll("[data-image-input]").forEach((input) => {
  input.addEventListener("change", () => {
    const file = input.files?.[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
      input.setCustomValidity("Choose an image smaller than 5 MB.");
      input.reportValidity();
      input.value = "";
      return;
    }
    input.setCustomValidity("");
  });
});