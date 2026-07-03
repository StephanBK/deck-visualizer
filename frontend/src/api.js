// All talk with the FastAPI backend lives here.
// Same-origin in prod (FastAPI serves dist/); proxied by Vite in dev.

export class AuthError extends Error {}

function pinHeaders(extra = {}) {
  const pin = localStorage.getItem("appPin");
  return pin ? { ...extra, "X-App-Pin": pin } : extra;
}

async function errorDetail(res, fallback) {
  try {
    const data = await res.json();
    if (data.detail) return String(data.detail);
  } catch {
    /* non-JSON error body */
  }
  return fallback;
}

async function checkOk(res, fallback) {
  if (res.ok) return;
  if (res.status === 401) throw new AuthError("PIN required");
  const err = new Error(await errorDetail(res, fallback));
  err.status = res.status;
  throw err;
}

export async function verifyPin(pin) {
  const res = await fetch("/api/auth", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pin }),
  });
  if (res.status === 401) return false;
  await checkOk(res, "Couldn't verify PIN");
  return true;
}

export async function fetchMaterials() {
  const res = await fetch("/api/materials", { headers: pinHeaders() });
  await checkOk(res, `Couldn't load materials (${res.status})`);
  const data = await res.json();
  return data.materials ?? data;
}

// Downscale + re-encode a photo to JPEG in the browser before upload.
// Two birds: shrinks 4-8 MB iPad photos, and converts HEIC (which Safari can
// decode natively) into JPEG the backend understands.
export async function compressImage(file, maxSide = 1600) {
  try {
    const bitmap = await createImageBitmap(file);
    const scale = Math.min(1, maxSide / Math.max(bitmap.width, bitmap.height));
    const w = Math.round(bitmap.width * scale);
    const h = Math.round(bitmap.height * scale);
    const canvas = document.createElement("canvas");
    canvas.width = w;
    canvas.height = h;
    canvas.getContext("2d").drawImage(bitmap, 0, 0, w, h);
    bitmap.close();
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.9));
    if (!blob) throw new Error("encode failed");
    const base = (file.name || "photo").replace(/\.[^.]+$/, "");
    return new File([blob], `${base}.jpg`, { type: "image/jpeg" });
  } catch {
    return file; // fall back to the original; the backend validates anyway
  }
}

export async function renderPhoto(file, { materialId, mode, declutter, stageFurniture, projectId }, signal) {
  const fd = new FormData();
  fd.append("photo", file);
  fd.append("material_id", materialId);
  fd.append("mode", mode);
  fd.append("declutter", String(declutter));
  fd.append("stage_furniture", String(stageFurniture));
  if (projectId) fd.append("project_id", projectId);
  const res = await fetch("/api/render", { method: "POST", body: fd, headers: pinHeaders(), signal });
  await checkOk(res, `Render failed (${res.status})`);
  return res.json();
}

export async function createHero(resultNames, materialId, projectId) {
  const res = await fetch("/api/fusion", {
    method: "POST",
    headers: pinHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({
      result_names: resultNames,
      material_id: materialId || null,
      project_id: projectId || null,
    }),
  });
  await checkOk(res, `Hero render failed (${res.status})`);
  return res.json();
}

export async function createProject(name) {
  const res = await fetch("/api/projects", {
    method: "POST",
    headers: pinHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ name }),
  });
  await checkOk(res, "Couldn't create project");
  return res.json();
}

export async function listProjects() {
  const res = await fetch("/api/projects", { headers: pinHeaders() });
  await checkOk(res, "Couldn't load projects");
  return (await res.json()).projects;
}

export async function getProject(id) {
  const res = await fetch(`/api/projects/${id}`, { headers: pinHeaders() });
  await checkOk(res, "Couldn't load project");
  return res.json();
}

// Native share sheet (Mail / Messages / WhatsApp on iPad). Returns false when
// the browser can't share files — caller should fall back to download.
export async function shareImage(url, text) {
  try {
    const res = await fetch(url);
    const blob = await res.blob();
    const file = new File([blob], url.split("/").pop() || "deck.jpg", { type: "image/jpeg" });
    if (navigator.canShare && navigator.canShare({ files: [file] })) {
      await navigator.share({ files: [file], text });
      return true;
    }
  } catch (e) {
    if (e.name === "AbortError") return true; // user closed the sheet — not an error
  }
  return false;
}
