const api = typeof browser !== "undefined" ? browser : chrome;

const adminBtn = document.getElementById("admin-btn");
const statusEl = document.getElementById("status");
const otpListEl = document.getElementById("otp-list");
const timerEl = document.getElementById("timer");
const searchInput = document.getElementById("search");

let services = [];
let suggestedIds = new Set();
let timerHandle = null;

function setStatus(message, isError = false) {
  statusEl.textContent = message || "";
  statusEl.style.color = isError ? "#f87171" : "#94a3b8";
}

function base32ToBytes(base32) {
  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
  const cleaned = base32.toUpperCase().replace(/=+$/u, "").replace(/[^A-Z2-7]/gu, "");
  let bits = "";
  for (const char of cleaned) {
    const val = alphabet.indexOf(char);
    if (val === -1) {
      continue;
    }
    bits += val.toString(2).padStart(5, "0");
  }
  const bytes = [];
  for (let i = 0; i + 8 <= bits.length; i += 8) {
    bytes.push(parseInt(bits.slice(i, i + 8), 2));
  }
  return new Uint8Array(bytes);
}

async function generateTotp(service) {
  const digits = service.digits || 6;
  const period = service.period || 30;
  let counter = Math.floor(Date.now() / 1000 / period);
  const counterBytes = new Uint8Array(8);
  for (let i = 7; i >= 0; i -= 1) {
    counterBytes[i] = counter & 0xff;
    counter >>= 8;
  }

  const keyBytes = base32ToBytes(service.secret || "");
  const cryptoKey = await crypto.subtle.importKey(
    "raw",
    keyBytes,
    { name: "HMAC", hash: "SHA-1" },
    false,
    ["sign"]
  );

  const signature = new Uint8Array(await crypto.subtle.sign("HMAC", cryptoKey, counterBytes));
  const offset = signature[signature.length - 1] & 0x0f;
  const binary =
    ((signature[offset] & 0x7f) << 24) |
    ((signature[offset + 1] & 0xff) << 16) |
    ((signature[offset + 2] & 0xff) << 8) |
    (signature[offset + 3] & 0xff);
  const otp = (binary % 10 ** digits).toString().padStart(digits, "0");
  return otp;
}

function timeLeft(period = 30) {
  const seconds = Math.floor(Date.now() / 1000);
  return period - (seconds % period);
}

function renderServices(filter = "") {
  otpListEl.innerHTML = "";
  const filtered = services.filter((service) => {
    const query = filter.trim().toLowerCase();
    if (!query) {
      return true;
    }
    const text = `${service.name} ${service.account || ""}`.toLowerCase();
    return text.includes(query);
  });

  if (!filtered.length) {
    otpListEl.innerHTML = "<div class=\"status\">Sin servicios.</div>";
    return;
  }

  filtered.forEach((service) => {
    const item = document.createElement("div");
    item.className = "otp-item";
    
    if (suggestedIds.has(service.id)) {
      item.classList.add("suggested");
    }

    item.addEventListener("click", async () => {
      try {
        const otp = await generateTotp(service);
        const [tab] = await api.tabs.query({ active: true, currentWindow: true });
        if (!tab?.id) {
          setStatus("No hay pestaña activa.", true);
          return;
        }
        await api.tabs.sendMessage(tab.id, { type: "fill-otp", otp });
        setStatus(`Autofill enviado a ${service.name}`);
      } catch (err) {
        setStatus("No se pudo hacer autofill.", true);
      }
    });

    const left = document.createElement("div");
    left.className = "otp-left";

    const title = document.createElement("h3");
    title.textContent = service.name;

    const meta = document.createElement("div");
    meta.className = "otp-meta";
    meta.textContent = service.account ? `Cuenta: ${service.account}` : `Período: ${service.period || 30}s`;

    const code = document.createElement("div");
    code.className = "otp-code";
    code.textContent = "······";

    const actions = document.createElement("div");
    actions.className = "otp-actions";

    const copyBtn = document.createElement("button");
    copyBtn.className = "icon-btn copy-btn";
    copyBtn.title = "Copiar OTP";
    copyBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>';
    copyBtn.addEventListener("click", async (event) => {
      event.stopPropagation();
      try {
        const otp = await generateTotp(service);
        await navigator.clipboard.writeText(otp);
        setStatus(`Copiado ${service.name}`);
      } catch (err) {
        setStatus("No se pudo copiar el OTP.", true);
      }
    });

    actions.append(copyBtn);
    left.append(title, meta, code);
    item.append(left, actions);
    otpListEl.appendChild(item);

    item.dataset.serviceId = service.id;
    item.dataset.period = service.period || 30;
  });

  updateCodes();
}

async function updateCodes() {
  const items = Array.from(document.querySelectorAll(".otp-item"));
  await Promise.all(
    items.map(async (item) => {
      const service = services.find((s) => s.id === item.dataset.serviceId);
      if (!service) {
        return;
      }
      const codeEl = item.querySelector(".otp-code");
      if (!codeEl) {
        return;
      }
      const otp = await generateTotp(service);
      codeEl.textContent = otp;
    })
  );

  if (services.length) {
    const defaultPeriod = services[0]?.period || 30;
    timerEl.textContent = `⏱ ${timeLeft(defaultPeriod)}s`;
  } else {
    timerEl.textContent = "";
  }
}

function startTimer() {
  if (timerHandle) {
    clearInterval(timerHandle);
  }
  timerHandle = setInterval(updateCodes, 1000);
}

async function loadExistingServices() {
  try {
    const [tab] = await api.tabs.query({ active: true, currentWindow: true });
    let currentHostname = "";
    
    // Try to get hostname from tab URL directly
    if (tab?.url) {
      try {
        const url = new URL(tab.url);
        currentHostname = url.hostname || "";
      } catch (err) {
        // Invalid URL
      }
    }
    
    // Fallback: try content script if tab URL not available
    if (!currentHostname && tab?.id) {
      try {
        const response = await api.tabs.sendMessage(tab.id, { type: "get-current-url" });
        currentHostname = response?.url || "";
      } catch (err) {
        // Content script might not be available
      }
    }

    const response = await api.runtime.sendMessage({ type: "get-services" });
    if (response?.ok) {
      services = response.services || [];
      suggestedIds.clear();
      
      // Sort services: suggested first (matching current hostname), then rest
      if (currentHostname) {
        const suggested = services.filter(s => 
          s.name.toLowerCase().includes(currentHostname.toLowerCase()) ||
          (s.account && s.account.toLowerCase().includes(currentHostname.toLowerCase()))||
          (s.account && s.account.split("@")[1]?.split(".")[0]?.toLowerCase().includes(currentHostname.toLowerCase()))
        );
        suggested.forEach(s => suggestedIds.add(s.id));
        const others = services.filter(s => !suggested.includes(s));
        services = [...suggested, ...others];
      }
      
      renderServices(searchInput.value);
      startTimer();
      setStatus("Servicios cargados.");
    } else if (response?.needsUnlock) {
      setStatus("Archivo cargado. Desbloquea en Ajustes.");
      document.querySelector(".toolbar").style.display = "none";
      const noFile = document.createElement("div");
      noFile.className = "no-file";
      noFile.innerHTML = `
        <p>Carga y desbloquea tu archivo .2fas desde Ajustes.</p>
        <button id="open-admin-from-popup" class="primary-btn">Abrir Ajustes</button>
      `;
      document.querySelector(".otp-panel").insertBefore(noFile, document.querySelector(".otp-list"));
      document.getElementById("open-admin-from-popup").addEventListener("click", async () => {
        const url = api.runtime.getURL("manage.html");
        await api.tabs.create({ url });
      });
    } else {
      setStatus("Carga un archivo en Ajustes.");
      document.querySelector(".toolbar").style.display = "none";
      const noFile = document.createElement("div");
      noFile.className = "no-file";
      noFile.innerHTML = `
        <p>Carga tu archivo .2fas para empezar.</p>
        <button id="open-admin-from-popup" class="primary-btn">Abrir Ajustes</button>
      `;
      document.querySelector(".otp-panel").insertBefore(noFile, document.querySelector(".otp-list"));
      document.getElementById("open-admin-from-popup").addEventListener("click", async () => {
        const url = api.runtime.getURL("manage.html");
        await api.tabs.create({ url });
      });
    }
  } catch (err) {
    setStatus("Error al cargar servicios.");
  }
}

adminBtn.addEventListener("click", async () => {
  const url = api.runtime.getURL("manage.html");
  await api.tabs.create({ url });
});

searchInput.addEventListener("input", () => {
  renderServices(searchInput.value);
});

loadExistingServices();
