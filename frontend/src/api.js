// All talk with the FastAPI backend lives here.
// Same-origin in prod (FastAPI serves dist/); proxied by Vite in dev.

async function errorDetail(res, fallback) {
  try {
    const data = await res.json();
    if (data.detail) return String(data.detail);
  } catch {
    /* non-JSON error body */
  }
  return fallback;
}

export async function fetchMaterials() {
  const res = await fetch("/api/materials");
  if (!res.ok) throw new Error(await errorDetail(res, `Couldn't load materials (${res.status})`));
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

export async function renderPhoto(file, { materialId, mode, declutter, stageFurniture }) {
  const fd = new FormData();
  fd.append("photo", file);
  fd.append("material_id", materialId);
  fd.append("mode", mode);
  fd.append("declutter", String(declutter));
  fd.append("stage_furniture", String(stageFurniture));
  const res = await fetch("/api/render", { method: "POST", body: fd });
  if (!res.ok) throw new Error(await errorDetail(res, `Render failed (${res.status})`));
  return res.json();
}

export async function createHero(resultNames, materialId) {
  const res = await fetch("/api/fusion", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ result_names: resultNames, material_id: materialId || null }),
  });
  if (!res.ok) throw new Error(await errorDetail(res, `Hero render failed (${res.status})`));
  return res.json();
}
