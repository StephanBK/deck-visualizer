"""
gemini_edit.py  —  the heart of the app: one deck photo + one swatch -> one edit.

This sends THREE things to Gemini's image model (the "Nano Banana" family,
which is the part of Gemini that accepts reference images):
    1. the customer's deck photo   (what to edit)
    2. the supplier swatch image   (what to apply)
    3. a text instruction          (what to change + what to keep)

The model returns the edited image as base64 data tucked inside the response
"parts". We iterate over the parts to find the image — we do NOT assume it's
at a fixed position, because the model sometimes adds a text part too.

SETUP (one-time):
    export GEMINI_API_KEY="your_free_AI_Studio_key"
Get a key free at https://aistudio.google.com/apikey  (no credit card; ~500 imgs/day).
"""

import base64
import io
import os
import time

import requests
from PIL import Image

# Start model from the build plan. If the API rejects it, this one line is the
# only thing to change. Upgrade paths: gemini-3.1-flash-image, gemini-3-pro-image.
MODEL = "gemini-2.5-flash-image"
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"


class GeminiError(RuntimeError):
    pass


def _img_to_b64_jpeg(path, max_side=1280):
    """Load an image, downscale a touch (keeps requests small/fast), return base64 JPEG."""
    im = Image.open(path).convert("RGB")
    if max(im.size) > max_side:
        im.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=92)
    return base64.b64encode(buf.getvalue()).decode()


def _extract_image(resp_json):
    """Find the first image part in the response; return a PIL image.

    Handles both snake_case (inline_data) and camelCase (inlineData) — the REST
    API has used both depending on version, so we check for either.
    """
    candidates = resp_json.get("candidates") or []
    if not candidates:
        raise GeminiError(f"No candidates in response: {resp_json}")
    parts = candidates[0].get("content", {}).get("parts", []) or []
    texts = []
    for p in parts:
        inline = p.get("inline_data") or p.get("inlineData")
        if inline and inline.get("data"):
            raw = base64.b64decode(inline["data"])
            return Image.open(io.BytesIO(raw)).convert("RGB")
        if p.get("text"):
            texts.append(p["text"])
    # No image came back — surface any text the model returned (usually explains why).
    note = " | ".join(texts) if texts else "no image and no text returned"
    raise GeminiError(f"Model returned no image. Model said: {note}")


def edit_deck_photo(deck_photo_path, swatch_path, instruction, retries=1):
    """Return a PIL image: the deck photo edited to wear the swatch material."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise GeminiError(
            "GEMINI_API_KEY not set. Run:  export GEMINI_API_KEY='your_key'\n"
            "Get a free key at https://aistudio.google.com/apikey"
        )

    payload = {
        "contents": [{
            "parts": [
                {"text": instruction},
                {"inline_data": {"mime_type": "image/jpeg",
                                 "data": _img_to_b64_jpeg(deck_photo_path)}},
                {"inline_data": {"mime_type": "image/jpeg",
                                 "data": _img_to_b64_jpeg(swatch_path)}},
            ]
        }],
        # Ask explicitly for an image back. If the API errors on this field,
        # try removing it or switching casing to ["Image","Text"].
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]},
    }
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}

    last_err = None
    for attempt in range(retries + 1):
        try:
            r = requests.post(ENDPOINT, headers=headers, json=payload, timeout=90)
            if r.status_code != 200:
                raise GeminiError(f"HTTP {r.status_code}: {r.text[:400]}")
            return _extract_image(r.json())
        except (requests.RequestException, GeminiError) as e:
            last_err = e
            if attempt < retries:
                time.sleep(1.5)
                continue
            raise
    raise last_err  # unreachable, but explicit
