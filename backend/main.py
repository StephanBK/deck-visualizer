"""
main.py — FastAPI backend for the deck visualizer.

WHAT A BACKEND IS (and why the iPad needs one):
  The iPad app can't run Python and must never hold the Gemini key. So it talks
  to THIS server over HTTP. The server holds the key, runs the render engine
  (the same edit_deck_photo() you tested on your Mac), and sends images back.
  It's the bridge between the tablet and Gemini.

ENDPOINTS:
  GET  /api/materials        -> the catalog (so the app can build the picker)
  GET  /api/swatches/<file>  -> a swatch image (served as a static file)
  POST /api/render           -> upload a deck photo + material_id (+ mode/toggles),
                                get a rendered image URL
  POST /api/fusion           -> combine 1-3 rendered results into one hero shot
  GET  /api/results/<file>   -> a rendered image (served as a static file)
  GET  /healthz              -> simple health check
  GET  /docs                 -> auto-generated interactive API tester (FastAPI gives this free)

RUN LOCALLY:
  cd backend
  pip3 install -r requirements.txt
  uvicorn main:app --reload --port 8000
  open http://localhost:8000/docs

ENV VARS:
  GEMINI_API_KEY    (required) Gemini key; set in Railway Variables in prod.
  ALLOWED_ORIGINS   (optional) comma-separated origins for CORS. Unset = no CORS
                    middleware at all, which is correct when the frontend is
                    served same-origin by this server (prod) or proxied (Vite dev).
  MAX_UPLOAD_MB     (optional) upload size cap, default 15.
  RESULT_TTL_HOURS  (optional) delete results older than this, default 24.
                    (Railway's disk is ephemeral anyway — reps should use the
                    download button for anything they want to keep.)
"""

import io
import os
import sys
import time
import uuid

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from PIL import Image
from starlette.concurrency import run_in_threadpool

# --- make the render engine (in ../render) importable from here ---
HERE = os.path.dirname(os.path.abspath(__file__))
RENDER_DIR = os.path.normpath(os.path.join(HERE, "..", "render"))
CATALOG_DIR = os.path.normpath(os.path.join(HERE, "..", "catalog"))
SWATCH_DIR = os.path.join(CATALOG_DIR, "swatches")
RESULTS_DIR = os.path.join(HERE, "results")
UPLOAD_DIR = os.path.join(HERE, "uploads")
FRONTEND_DIST = os.path.normpath(os.path.join(HERE, "..", "frontend", "dist"))
sys.path.insert(0, RENDER_DIR)

import prompt_builder as pb                             # noqa: E402
from gemini_edit import generate_image, GeminiError     # noqa: E402

os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_UPLOAD_MB = float(os.environ.get("MAX_UPLOAD_MB", "15"))
RESULT_TTL_HOURS = float(os.environ.get("RESULT_TTL_HOURS", "24"))

app = FastAPI(title="Deck Visualizer API", version="0.2")

# CORS: only needed if the frontend is ever served from a DIFFERENT origin.
# In production this server serves the frontend itself (same origin), and in
# dev the Vite server proxies /api here — so by default no CORS is enabled.
_origins = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()]
if _origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def cleanup_old_results():
    """Delete rendered results older than RESULT_TTL_HOURS (best-effort)."""
    cutoff = time.time() - RESULT_TTL_HOURS * 3600
    try:
        for name in os.listdir(RESULTS_DIR):
            path = os.path.join(RESULTS_DIR, name)
            if name != ".gitkeep" and os.path.isfile(path) and os.path.getmtime(path) < cutoff:
                os.remove(path)
    except OSError:
        pass


cleanup_old_results()

# Serve swatch images and rendered results directly as files.
app.mount("/api/swatches", StaticFiles(directory=SWATCH_DIR), name="swatches")
app.mount("/api/results", StaticFiles(directory=RESULTS_DIR), name="results")


@app.get("/api/status")
def root():
    return {"service": "Deck Visualizer API", "test_it": "/docs",
            "endpoints": ["/api/materials", "/api/render", "/api/fusion", "/healthz"]}


@app.get("/healthz")
def healthz():
    return {"status": "ok", "materials": len(pb.load_catalog())}


@app.get("/api/materials")
def list_materials():
    """Return the catalog, with a ready-to-use swatch URL added to each record."""
    mats = pb.load_catalog()
    for m in mats:
        m["swatch_url"] = f"/api/swatches/{os.path.basename(m['swatch_path'])}"
    return {"count": len(mats), "materials": mats}


def _save_result(img) -> str:
    """Save a rendered PIL image into RESULTS_DIR; return its filename."""
    name = f"{uuid.uuid4().hex}.jpg"
    img.save(os.path.join(RESULTS_DIR, name), quality=90)
    return name


@app.post("/api/render")
async def render(
    photo: UploadFile = File(...),
    material_id: str = Form(...),
    mode: str = Form("resurface"),
    declutter: bool = Form(False),
    stage_furniture: bool = Form(False),
):
    """Upload a deck photo + a material id (+ options) -> URL of the rendered image."""
    # 1. validate inputs
    if mode not in pb.MODES:
        raise HTTPException(status_code=400, detail=f"Unknown mode: {mode!r}")
    try:
        material = pb.get_material(material_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown material_id: {material_id}")

    data = await photo.read()
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413,
                            detail=f"Photo too large (max {MAX_UPLOAD_MB:g} MB)")
    try:
        Image.open(io.BytesIO(data)).verify()
    except Exception:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image")

    # 2. save the uploaded photo so the engine can read it from disk
    ext = os.path.splitext(photo.filename or "")[1].lower() or ".jpg"
    upload_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")
    with open(upload_path, "wb") as f:
        f.write(data)

    # 3. run the render engine in a worker thread — the Gemini call blocks for
    #    up to 90s, and running it inline would freeze the whole event loop
    #    (no health checks, no static files, no concurrent renders).
    swatch = pb.swatch_abs_path(material)
    instruction = pb.build_instruction(material, mode=mode,
                                       declutter=declutter,
                                       stage_furniture=stage_furniture)
    try:
        result_img = await run_in_threadpool(
            generate_image, [upload_path, swatch], instruction)
    except GeminiError as e:
        raise HTTPException(status_code=502, detail=f"Render failed: {e}")
    finally:
        try:
            os.remove(upload_path)   # we don't need to keep the upload
        except OSError:
            pass

    # 4. save the result and hand back its URL
    cleanup_old_results()
    result_name = _save_result(result_img)

    return JSONResponse({
        "render_id": os.path.splitext(result_name)[0],
        "material": {
            "id": material["id"],
            "name": material["name"],
            "brand": material["brand"],
            "collection": material["collection"],
            "swatch_source": material["swatch_source"],
        },
        "mode": mode,
        "after_url": f"/api/results/{result_name}",
    })


class FusionRequest(BaseModel):
    result_names: list[str] = Field(..., min_length=1, max_length=3)
    material_id: str | None = None


@app.post("/api/fusion")
async def fusion(req: FusionRequest):
    """Combine 1-3 already-rendered results into one polished marketing hero shot."""
    paths = []
    for name in req.result_names:
        safe = os.path.basename(name)          # no path tricks
        path = os.path.join(RESULTS_DIR, safe)
        if not os.path.isfile(path):
            raise HTTPException(status_code=404, detail=f"Unknown result: {safe}")
        paths.append(path)

    material = None
    if req.material_id:
        try:
            material = pb.get_material(req.material_id)
        except KeyError:
            raise HTTPException(status_code=404,
                                detail=f"Unknown material_id: {req.material_id}")

    instruction = pb.build_fusion_instruction(material)
    try:
        hero_img = await run_in_threadpool(generate_image, paths, instruction)
    except GeminiError as e:
        raise HTTPException(status_code=502, detail=f"Hero render failed: {e}")

    hero_name = f"hero_{uuid.uuid4().hex}.jpg"
    hero_img.save(os.path.join(RESULTS_DIR, hero_name), quality=90)
    return JSONResponse({"hero_url": f"/api/results/{hero_name}"})


# Serve the built frontend (frontend/dist) at the root. MUST be the last route:
# FastAPI matches top-to-bottom, and this mount would swallow /api/* otherwise.
# Guarded so the API still runs when dist/ hasn't been built yet.
if os.path.isdir(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
