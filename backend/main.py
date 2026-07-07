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
  POST /api/render           -> upload a deck photo + material_id (+ mode/toggles,
                                optional project_id), get a rendered image URL
  POST /api/fusion           -> combine 1-3 rendered results into one hero shot
  POST /api/auth             -> validate the app PIN (when APP_PIN is set)
  GET/POST /api/projects     -> saved customer projects (renders persist per project)
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
  APP_PIN           (optional) when set, API calls need it in the X-App-Pin
                    header; the frontend asks for it once and remembers it.
  DATA_DIR          (optional) persistent dir (Railway volume, e.g. /data) for
                    results, projects, and the spend counter.
  MAX_RENDERS_PER_DAY / MAX_RENDERS_PER_MONTH  (optional) hard spend cap on
                    Gemini calls (~$0.04 each). Defaults 50/day, 500/month
                    (= about $20/mo). When exhausted the API returns 429
                    instead of calling Gemini. Counter lives in a local file,
                    so it resets on redeploy — it's a safety net against
                    runaway/abusive use, not accounting.
"""

import io
import json
import os
import sys
import time
import uuid

from fastapi import Depends, FastAPI, UploadFile, File, Form, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from PIL import Image, ImageDraw, ImageFont
from starlette.concurrency import run_in_threadpool

# --- make the render engine (in ../render) importable from here ---
HERE = os.path.dirname(os.path.abspath(__file__))
RENDER_DIR = os.path.normpath(os.path.join(HERE, "..", "render"))
CATALOG_DIR = os.path.normpath(os.path.join(HERE, "..", "catalog"))
SWATCH_DIR = os.path.join(CATALOG_DIR, "swatches")
# DATA_DIR: set to a persistent mount (e.g. Railway volume at /data) so
# results, saved projects, and the spend counter survive redeploys.
DATA_DIR = os.environ.get("DATA_DIR") or HERE
RESULTS_DIR = os.path.join(DATA_DIR, "results")
PROJECTS_DIR = os.path.join(DATA_DIR, "projects")
UPLOAD_DIR = os.path.join(HERE, "uploads")
FRONTEND_DIST = os.path.normpath(os.path.join(HERE, "..", "frontend", "dist"))
sys.path.insert(0, RENDER_DIR)

import prompt_builder as pb                                            # noqa: E402
from gemini_edit import generate_image, analyze_audio, GeminiError     # noqa: E402

os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(PROJECTS_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_UPLOAD_MB = float(os.environ.get("MAX_UPLOAD_MB", "15"))
RESULT_TTL_HOURS = float(os.environ.get("RESULT_TTL_HOURS", "24"))
MAX_RENDERS_PER_DAY = int(os.environ.get("MAX_RENDERS_PER_DAY", "50"))
MAX_RENDERS_PER_MONTH = int(os.environ.get("MAX_RENDERS_PER_MONTH", "500"))
USAGE_PATH = os.path.join(DATA_DIR, "usage_counts.json")
# APP_PIN: when set, every data/render API call must carry it in the
# X-App-Pin header. Unset (local dev) = the gate is off.
APP_PIN = os.environ.get("APP_PIN", "").strip()

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


def require_pin(x_app_pin: str = Header(default="")):
    """Gate for API endpoints. No-op when APP_PIN is unset (local dev)."""
    if APP_PIN and x_app_pin != APP_PIN:
        raise HTTPException(status_code=401, detail="PIN required")


DISCLAIMER = "AI VISUALIZATION - NOT A PHOTOGRAPH"  # plain hyphen: the PIL default font has no em-dash glyph


def stamp_disclaimer(img):
    """Bake the AI disclaimer into the image itself, bottom-right. The UI badge
    is only an overlay — downloaded/shared files must carry the label too."""
    img = img.convert("RGB")
    d = ImageDraw.Draw(img, "RGBA")
    size = max(13, img.width // 60)
    try:
        font = ImageFont.load_default(size=size)
    except TypeError:  # older Pillow: fixed-size bitmap font
        font = ImageFont.load_default()
    tw = d.textlength(DISCLAIMER, font=font)
    pad = max(6, size // 2)
    x1, y1 = img.width - 10, img.height - 10
    x0, y0 = x1 - tw - pad * 2, y1 - size - pad * 2
    d.rounded_rectangle([x0, y0, x1, y1], radius=6, fill=(0, 0, 0, 130))
    d.text((x0 + pad, y0 + pad), DISCLAIMER, font=font, fill=(255, 255, 255, 225))
    return img


# ---------------- projects (persistent customer sessions) ----------------

def _project_path(pid):
    safe = os.path.basename(pid)
    if not safe.replace("-", "").isalnum():
        raise HTTPException(status_code=400, detail="Bad project id")
    return os.path.join(PROJECTS_DIR, f"{safe}.json")


def load_project(pid):
    try:
        with open(_project_path(pid)) as f:
            return json.load(f)
    except (OSError, ValueError):
        raise HTTPException(status_code=404, detail=f"Unknown project: {pid}")


def save_project(proj):
    proj["updated_at"] = time.time()
    with open(_project_path(proj["id"]), "w") as f:
        json.dump(proj, f)


def _read_usage():
    try:
        with open(USAGE_PATH) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def take_render_slot():
    """Hard spend cap: count every Gemini call, refuse with 429 once the daily
    or monthly budget is used up. Called from the (single-threaded) event loop
    BEFORE the render is dispatched, so check+increment can't race."""
    day = time.strftime("%Y-%m-%d")
    month = day[:7]
    usage = _read_usage()
    today, this_month = usage.get(day, 0), usage.get(month, 0)
    if today >= MAX_RENDERS_PER_DAY:
        raise HTTPException(
            status_code=429,
            detail=f"Daily render budget used up ({MAX_RENDERS_PER_DAY}/day). Try again tomorrow.")
    if this_month >= MAX_RENDERS_PER_MONTH:
        raise HTTPException(
            status_code=429,
            detail=f"Monthly render budget used up ({MAX_RENDERS_PER_MONTH}/month).")
    try:
        with open(USAGE_PATH, "w") as f:
            # only the current day + month keys are needed; old ones fall away
            json.dump({day: today + 1, month: this_month + 1}, f)
    except OSError:
        pass  # never block renders on a bookkeeping failure


def cleanup_old_results():
    """Delete rendered results older than RESULT_TTL_HOURS (best-effort)."""
    cutoff = time.time() - RESULT_TTL_HOURS * 3600
    try:
        for name in os.listdir(RESULTS_DIR):
            path = os.path.join(RESULTS_DIR, name)
            if name.startswith("p_"):
                continue  # files linked to a saved project are kept forever
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
    day = time.strftime("%Y-%m-%d")
    usage = _read_usage()
    return {
        "status": "ok",
        "materials": len(pb.load_catalog()),
        "renders_today": f"{usage.get(day, 0)}/{MAX_RENDERS_PER_DAY}",
        "renders_this_month": f"{usage.get(day[:7], 0)}/{MAX_RENDERS_PER_MONTH}",
    }


class AuthRequest(BaseModel):
    pin: str


@app.post("/api/auth")
def auth(req: AuthRequest):
    """Lets the frontend validate a PIN once before storing it locally."""
    if APP_PIN and req.pin != APP_PIN:
        raise HTTPException(status_code=401, detail="Wrong PIN")
    return {"ok": True, "pin_required": bool(APP_PIN)}


@app.get("/api/materials", dependencies=[Depends(require_pin)])
def list_materials():
    """Return the catalog, with a ready-to-use swatch URL added to each record."""
    mats = pb.load_catalog()
    for m in mats:
        m["swatch_url"] = f"/api/swatches/{os.path.basename(m['swatch_path'])}"
    return {"count": len(mats), "materials": mats}


# ---------------- project endpoints ----------------

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)


@app.post("/api/projects", dependencies=[Depends(require_pin)])
def create_project(req: ProjectCreate):
    proj = {
        "id": uuid.uuid4().hex[:12],
        "name": req.name.strip(),
        "created_at": time.time(),
        "updated_at": time.time(),
        "items": [],    # appended by /api/render when project_id is passed
        "heroes": [],   # appended by /api/fusion
    }
    save_project(proj)
    return {"id": proj["id"], "name": proj["name"]}


@app.get("/api/projects", dependencies=[Depends(require_pin)])
def list_projects():
    out = []
    try:
        names = os.listdir(PROJECTS_DIR)
    except OSError:
        names = []
    for name in names:
        if not name.endswith(".json"):
            continue
        try:
            with open(os.path.join(PROJECTS_DIR, name)) as f:
                p = json.load(f)
            out.append({
                "id": p["id"], "name": p["name"],
                "created_at": p["created_at"], "updated_at": p["updated_at"],
                "item_count": len(p.get("items", [])),
                "cover_url": (p.get("items") or [{}])[-1].get("after_url"),
            })
        except (OSError, ValueError, KeyError):
            continue
    out.sort(key=lambda p: p["updated_at"], reverse=True)
    return {"projects": out}


@app.get("/api/projects/{pid}", dependencies=[Depends(require_pin)])
def get_project(pid: str):
    return load_project(pid)


@app.post("/api/render", dependencies=[Depends(require_pin)])
async def render(
    photo: UploadFile = File(...),
    material_id: str = Form(...),
    mode: str = Form("resurface"),
    declutter: bool = Form(False),
    stage_furniture: bool = Form(False),
    custom_instructions: str = Form(""),
    project_id: str = Form(None),
):
    """Upload a deck photo + a material id (+ options) -> URL of the rendered image."""
    # 1. validate inputs
    if mode not in pb.MODES:
        raise HTTPException(status_code=400, detail=f"Unknown mode: {mode!r}")
    try:
        material = pb.get_material(material_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown material_id: {material_id}")
    if project_id:
        load_project(project_id)  # 404s before burning budget (re-loaded fresh at save time)
    take_render_slot()

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
                                       stage_furniture=stage_furniture,
                                       custom_instructions=custom_instructions.strip()[:1000])
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

    # 4. stamp the AI disclaimer, save, and hand back the URL. Files that
    #    belong to a saved project get a p_ prefix (exempt from TTL cleanup).
    cleanup_old_results()
    result_img = stamp_disclaimer(result_img)
    hexid = uuid.uuid4().hex
    prefix = "p_" if project_id else ""
    result_name = f"{prefix}{hexid}.jpg"
    result_img.save(os.path.join(RESULTS_DIR, result_name), quality=90)

    before_url = None
    if project_id:
        before_name = f"p_{hexid}_before.jpg"
        Image.open(io.BytesIO(data)).convert("RGB").save(
            os.path.join(RESULTS_DIR, before_name), quality=88)
        before_url = f"/api/results/{before_name}"
        # Re-load fresh and append/save with no awaits in between: concurrent
        # renders into the same project must not clobber each other's items.
        project = load_project(project_id)
        project["items"].append({
            "before_url": before_url,
            "after_url": f"/api/results/{result_name}",
            "material_id": material["id"],
            "material_name": material["name"],
            "brand": material["brand"],
            "mode": mode,
            "created_at": time.time(),
        })
        save_project(project)

    return JSONResponse({
        "render_id": hexid,
        "material": {
            "id": material["id"],
            "name": material["name"],
            "brand": material["brand"],
            "collection": material["collection"],
            "swatch_source": material["swatch_source"],
        },
        "mode": mode,
        "after_url": f"/api/results/{result_name}",
        "before_url": before_url,
    })


class FusionRequest(BaseModel):
    result_names: list[str] = Field(..., min_length=1, max_length=3)
    material_id: str | None = None
    project_id: str | None = None


@app.post("/api/fusion", dependencies=[Depends(require_pin)])
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

    if req.project_id:
        load_project(req.project_id)  # validate before burning budget
    instruction = pb.build_fusion_instruction(material)
    take_render_slot()
    try:
        hero_img = await run_in_threadpool(generate_image, paths, instruction)
    except GeminiError as e:
        raise HTTPException(status_code=502, detail=f"Hero render failed: {e}")

    hero_img = stamp_disclaimer(hero_img)
    prefix = "p_" if req.project_id else ""
    hero_name = f"{prefix}hero_{uuid.uuid4().hex}.jpg"
    hero_img.save(os.path.join(RESULTS_DIR, hero_name), quality=90)
    hero_url = f"/api/results/{hero_name}"
    if req.project_id:
        # fresh load + sync append/save — same race note as /api/render
        project = load_project(req.project_id)
        project["heroes"].append({"hero_url": hero_url, "created_at": time.time()})
        save_project(project)
    return JSONResponse({"hero_url": hero_url})


TRANSCRIBE_PROMPT = (
    "You are listening to a recorded conversation between a deck-construction "
    "sales rep and a homeowner about the homeowner's deck project. "
    "Respond with STRICT JSON only — no markdown fences, no commentary — with "
    "exactly these keys:\n"
    '  "transcript": a clean transcript of the conversation,\n'
    '  "preferences": a list of short, actionable phrases describing how the '
    "customer wants the deck to LOOK or FUNCTION (colors, materials, style, "
    "features, things to keep or avoid). Only include preferences the customer "
    "actually expressed,\n"
    '  "summary": one short paragraph summarizing what the customer is looking for.'
)

MAX_AUDIO_MB = 20


def _parse_transcription(text):
    """Best-effort JSON parse of the model's reply; fall back to raw text so a
    sloppy response still gives the rep something to review and edit."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    try:
        data = json.loads(cleaned)
        return {
            "transcript": str(data.get("transcript", "")),
            "preferences": [str(p) for p in data.get("preferences", []) if str(p).strip()],
            "summary": str(data.get("summary", "")),
        }
    except ValueError:
        return {"transcript": text, "preferences": [], "summary": text[:300]}


@app.post("/api/transcribe", dependencies=[Depends(require_pin)])
async def transcribe(audio: UploadFile = File(...), project_id: str = Form(None)):
    """Recorded client conversation -> transcript + extracted deck preferences.
    The frontend shows these for review/editing before they touch a render."""
    if project_id:
        load_project(project_id)  # 404s before burning budget
    data = await audio.read()
    if len(data) > MAX_AUDIO_MB * 1024 * 1024:
        raise HTTPException(status_code=413,
                            detail=f"Recording too large (max {MAX_AUDIO_MB} MB)")
    if not data:
        raise HTTPException(status_code=400, detail="Empty recording")
    take_render_slot()  # transcription is cheap, but keep it under the spend cap

    mime = audio.content_type or "audio/mp4"
    audio_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}.audio")
    with open(audio_path, "wb") as f:
        f.write(data)
    try:
        text = await run_in_threadpool(analyze_audio, audio_path, mime, TRANSCRIBE_PROMPT)
    except GeminiError as e:
        raise HTTPException(status_code=502, detail=f"Transcription failed: {e}")
    finally:
        try:
            os.remove(audio_path)
        except OSError:
            pass

    result = _parse_transcription(text)
    if project_id:
        # fresh load + sync append/save — same race note as /api/render
        project = load_project(project_id)
        project.setdefault("notes", []).append({
            "transcript": result["transcript"],
            "summary": result["summary"],
            "created_at": time.time(),
        })
        save_project(project)
    return JSONResponse(result)


class RefineRequest(BaseModel):
    result_name: str
    instruction: str = Field(..., min_length=1, max_length=500)
    project_id: str | None = None


@app.post("/api/refine", dependencies=[Depends(require_pin)])
async def refine(req: RefineRequest):
    """Iterate on an already-rendered result with a free-text tweak
    ('make the railing white') -> URL of the new image."""
    safe = os.path.basename(req.result_name)   # no path tricks
    path = os.path.join(RESULTS_DIR, safe)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail=f"Unknown result: {safe}")
    if req.project_id:
        load_project(req.project_id)  # validate before burning budget
    instruction = pb.build_refine_instruction(req.instruction)
    take_render_slot()
    try:
        result_img = await run_in_threadpool(generate_image, [path], instruction)
    except GeminiError as e:
        raise HTTPException(status_code=502, detail=f"Refine failed: {e}")

    result_img = stamp_disclaimer(result_img)
    prefix = "p_" if req.project_id else ""
    result_name = f"{prefix}{uuid.uuid4().hex}.jpg"
    result_img.save(os.path.join(RESULTS_DIR, result_name), quality=90)
    after_url = f"/api/results/{result_name}"
    if req.project_id:
        # fresh load + sync append/save — same race note as /api/render
        project = load_project(req.project_id)
        project["items"].append({
            "before_url": f"/api/results/{safe}",
            "after_url": after_url,
            "material_id": None,
            "material_name": "Refined",
            "brand": "",
            "mode": "refine",
            "instruction": req.instruction,
            "created_at": time.time(),
        })
        save_project(project)
    return JSONResponse({"after_url": after_url})


# Serve the built frontend (frontend/dist) at the root. MUST be the last route:
# FastAPI matches top-to-bottom, and this mount would swallow /api/* otherwise.
# Guarded so the API still runs when dist/ hasn't been built yet.
if os.path.isdir(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
