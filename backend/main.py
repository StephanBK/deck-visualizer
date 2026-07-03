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
  POST /api/render           -> upload a deck photo + material_id, get a rendered image URL
  GET  /api/results/<file>   -> a rendered image (served as a static file)
  GET  /healthz              -> simple health check
  GET  /docs                 -> auto-generated interactive API tester (FastAPI gives this free)

RUN LOCALLY:
  cd backend
  pip3 install -r requirements.txt
  uvicorn main:app --reload --port 8000
  open http://localhost:8000/docs
"""

import os
import sys
import uuid

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# --- make the render engine (in ../render) importable from here ---
HERE = os.path.dirname(os.path.abspath(__file__))
RENDER_DIR = os.path.normpath(os.path.join(HERE, "..", "render"))
CATALOG_DIR = os.path.normpath(os.path.join(HERE, "..", "catalog"))
SWATCH_DIR = os.path.join(CATALOG_DIR, "swatches")
RESULTS_DIR = os.path.join(HERE, "results")
UPLOAD_DIR = os.path.join(HERE, "uploads")
sys.path.insert(0, RENDER_DIR)

import prompt_builder as pb                              # noqa: E402
from gemini_edit import edit_deck_photo, GeminiError     # noqa: E402

os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="Deck Visualizer API", version="0.1")

# CORS: the iPad web app runs on a DIFFERENT origin (domain) than this API.
# Browsers block cross-origin calls unless the server explicitly allows them.
# For development we allow all; we'll lock this to the real app domain in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve swatch images and rendered results directly as files.
app.mount("/api/swatches", StaticFiles(directory=SWATCH_DIR), name="swatches")
app.mount("/api/results", StaticFiles(directory=RESULTS_DIR), name="results")


@app.get("/api/status")
def root():
    return {"service": "Deck Visualizer API", "test_it": "/docs",
            "endpoints": ["/api/materials", "/api/render", "/healthz"]}


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


@app.post("/api/render")
async def render(photo: UploadFile = File(...), material_id: str = Form(...)):
    """Upload a deck photo + a material id -> returns a URL to the rendered image."""
    # 1. validate the chosen material
    try:
        material = pb.get_material(material_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown material_id: {material_id}")

    # 2. save the uploaded photo so the engine can read it from disk
    ext = os.path.splitext(photo.filename or "")[1].lower() or ".jpg"
    upload_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")
    with open(upload_path, "wb") as f:
        f.write(await photo.read())

    # 3. run the render engine (the exact code you tested on your Mac)
    swatch = pb.swatch_abs_path(material)
    instruction = pb.build_instruction(material)
    try:
        result_img = edit_deck_photo(upload_path, swatch, instruction)
    except GeminiError as e:
        raise HTTPException(status_code=502, detail=f"Render failed: {e}")
    finally:
        try:
            os.remove(upload_path)   # we don't need to keep the upload
        except OSError:
            pass

    # 4. save the result and hand back its URL
    result_name = f"{uuid.uuid4().hex}.jpg"
    result_img.save(os.path.join(RESULTS_DIR, result_name), quality=90)

    return JSONResponse({
        "material": {
            "id": material["id"],
            "name": material["name"],
            "brand": material["brand"],
            "collection": material["collection"],
            "swatch_source": material["swatch_source"],
        },
        "after_url": f"/api/results/{result_name}",
    })
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
