const api = typeof browser !== "undefined" ? browser : chrome;

const fileInput = document.getElementById("file-input");
const loadFileBtn = document.getElementById("load-file");
const unlockBtn = document.getElementById("unlock");
const passphraseInput = document.getElementById("passphrase");
const statusEl = document.getElementById("status");
const unlockSection = document.getElementById("unlock-section");

function setStatus(message, isError = false) {
  statusEl.textContent = message || "";
  statusEl.style.color = isError ? "#f87171" : "#94a3af";
}

loadFileBtn.addEventListener("click", async () => {
  fileInput.click();
});

fileInput.addEventListener("change", async () => {
  const file = fileInput.files?.[0];
  if (!file) {
    setStatus("Selecciona un archivo .2fas.", true);
    return;
  }
  setStatus("Cargando archivo...");
  const text = await file.text();
  const result = await api.runtime.sendMessage({ type: "load-file", fileContent: text });
  if (result?.ok) {
    setStatus("Archivo cargado. Intentando desbloquear automáticamente...");
    
    // Try to auto-unlock with saved password
    const stored = await api.storage.local.get(["savedPassword"]);
    if (stored.savedPassword) {
      const response = await api.runtime.sendMessage({ type: "unlock", passphrase: stored.savedPassword });
      if (response?.ok) {
        setStatus("✓ Desbloqueado automáticamente. Cerrando...");
        await api.storage.local.set({ onboardingComplete: true });
        setTimeout(() => window.close(), 800);
      } else {
        unlockSection.style.display = "block";
        passphraseInput.focus();
        setStatus("⚠ Contraseña guardada inválida. Ingresa una nueva.");
      }
    } else {
      unlockSection.style.display = "block";
      passphraseInput.focus();
      setStatus("Por favor, ingresa la contraseña para desbloquear.");
    }
  } else {
    setStatus("Error: No se pudo cargar el archivo.", true);
  }
});

unlockBtn.addEventListener("click", async () => {
  const passphrase = passphraseInput.value;
  if (!passphrase) {
    setStatus("Por favor, ingresa la contraseña.", true);
    return;
  }
  setStatus("Desbloqueando...");
  const response = await api.runtime.sendMessage({ type: "unlock", passphrase });
  if (response?.ok) {
    // Save password for auto-unlock next time
    await api.storage.local.set({ savedPassword: passphrase });
    setStatus("✓ Servicios desbloqueados. Cerrando...");
    await api.storage.local.set({ onboardingComplete: true });
    setTimeout(() => window.close(), 800);
  } else {
    passphraseInput.value = "";
    passphraseInput.focus();
    setStatus(response?.error || "⚠ Contraseña incorrecta.", true);
  }
});
