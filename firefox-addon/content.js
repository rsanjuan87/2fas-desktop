const api = typeof browser !== "undefined" ? browser : chrome;

function fillActiveElement(value) {
  const active = document.activeElement;
  if (!active) {
    return false;
  }

  if (active.tagName === "INPUT" || active.tagName === "TEXTAREA") {
    active.focus();
    active.value = value;
    active.dispatchEvent(new Event("input", { bubbles: true }));
    active.dispatchEvent(new Event("change", { bubbles: true }));
    return true;
  }

  if (active.isContentEditable) {
    active.focus();
    active.textContent = value;
    active.dispatchEvent(new Event("input", { bubbles: true }));
    return true;
  }

  return false;
}

api.runtime.onMessage.addListener((message) => {
  if (message?.type === "fill-otp" && typeof message.otp === "string") {
    const ok = fillActiveElement(message.otp);
    return Promise.resolve({ ok });
  }
  return undefined;
});
