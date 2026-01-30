const api = typeof browser !== "undefined" ? browser : chrome;

let decryptedServices = null;
let cachedFileContent = null;

async function loadStoredFile() {
  const data = await api.storage.local.get(["fileContent"]);
  cachedFileContent = data.fileContent || null;
  return cachedFileContent;
}

// Check on first install or update
api.runtime.onInstalled.addListener(async (details) => {
  if (details.reason === "install") {
    const data = await api.storage.local.get(["onboardingComplete"]);
    if (!data.onboardingComplete) {
      api.tabs.create({ url: "onboarding.html" });
    }
  }
});

function base64ToBytes(base64) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

async function deriveAesKey(passphrase, salt) {
  const enc = new TextEncoder();
  const keyMaterial = await crypto.subtle.importKey(
    "raw",
    enc.encode(passphrase),
    { name: "PBKDF2" },
    false,
    ["deriveKey"]
  );
  return crypto.subtle.deriveKey(
    {
      name: "PBKDF2",
      salt,
      iterations: 10000,
      hash: "SHA-256"
    },
    keyMaterial,
    { name: "AES-GCM", length: 256 },
    false,
    ["decrypt"]
  );
}

async function decryptServices(encrypted, passphrase) {
  const [credentialsEncB64, saltB64, nonceB64] = encrypted.split(":");
  if (!credentialsEncB64 || !saltB64 || !nonceB64) {
    throw new Error("Formato de servicios encriptados inválido.");
  }
  const credentialsEnc = base64ToBytes(credentialsEncB64);
  const salt = base64ToBytes(saltB64);
  const nonce = base64ToBytes(nonceB64);

  const key = await deriveAesKey(passphrase, salt);
  let decrypted;
  try {
    decrypted = await crypto.subtle.decrypt(
      { name: "AES-GCM", iv: nonce },
      key,
      credentialsEnc
    );
  } catch (err) {
    throw new Error("Contraseña inválida.");
  }

  const jsonText = new TextDecoder().decode(new Uint8Array(decrypted));
  const data = JSON.parse(jsonText);
  if (!Array.isArray(data)) {
    throw new Error("Estructura inesperada en datos desencriptados.");
  }
  return data;
}

function normalizeServices(services) {
  return services.map((service, index) => {
    const otp = service.otp || {};
    return {
      id: service.id || `service-${index}`,
      name: service.name || otp.label || "(sin nombre)",
      account: otp.account || null,
      secret: service.secret,
      digits: otp.digits || 6,
      period: otp.period || 30
    };
  });
}

async function parse2fasFile(fileContent, passphrase) {
  let data;
  try {
    data = JSON.parse(fileContent);
  } catch (err) {
    throw new Error("El archivo no es un JSON válido.");
  }

  if (Array.isArray(data.services) && data.services.length > 0) {
    return normalizeServices(data.services);
  }

  if (!data.servicesEncrypted) {
    throw new Error("El archivo no contiene servicios.");
  }

  if (!passphrase) {
    throw new Error("Se requiere contraseña para desencriptar el archivo.");
  }

  const services = await decryptServices(data.servicesEncrypted, passphrase);
  return normalizeServices(services);
}

api.runtime.onMessage.addListener((message) => {
  if (!message || !message.type) {
    return undefined;
  }

  if (message.type === "load-file") {
    cachedFileContent = message.fileContent || null;
    decryptedServices = null;
    return api.storage.local
      .set({ fileContent: cachedFileContent })
      .then(() => ({ ok: true }));
  }

  if (message.type === "unlock") {
    return (async () => {
      const fileContent = cachedFileContent || (await loadStoredFile());
      if (!fileContent) {
        return { ok: false, error: "No hay archivo cargado." };
      }
      try {
        const services = await parse2fasFile(fileContent, message.passphrase || "");
        decryptedServices = services;
        return { ok: true, services };
      } catch (err) {
        return { ok: false, error: err.message || "Error al desencriptar." };
      }
    })();
  }

  if (message.type === "get-services") {
    return (async () => {
      if (decryptedServices) {
        return { ok: true, services: decryptedServices };
      }
      const fileContent = cachedFileContent || (await loadStoredFile());
      return { ok: false, needsUnlock: !!fileContent };
    })();
  }

  if (message.type === "forget") {
    decryptedServices = null;
    cachedFileContent = null;
    return api.storage.local.remove(["fileContent"]).then(() => ({ ok: true }));
  }

  return undefined;
});

loadStoredFile();
