"""
collect_catalog.py  —  builds the catalog from catalog_source.py.

WHAT IT DOES (run it; it's idempotent — safe to re-run):
  1. Reads every record from catalog_source.build_records().
  2. If the record has a real swatch_url -> downloads the image to swatches/<id>.jpg
     and marks swatch_source = "downloaded_real".
     If the download fails for any reason -> falls back to a placeholder so the
     catalog is never left with a missing swatch.
  3. If the record has no swatch_url -> generates a procedural wood-grain swatch
     tinted to the record's hex, saved as swatches/<id>.png, marked
     swatch_source = "generated_placeholder".
  4. Writes catalog_seed.json (the portable artifact that later loads into Postgres),
     including each swatch's local path, source, and pixel dimensions.
  5. Prints a summary.

TO ADD MORE REAL IMAGES LATER (the reproducible part):
  - Use harvest_swatch_urls.py to pull real URLs from a supplier product page,
    paste them into the matching rows in catalog_source.py, and re-run this file.
    The placeholders for those rows are replaced automatically.
"""

import io
import json
import os
import time

import numpy as np
import requests
from PIL import Image

import catalog_source

HERE = os.path.dirname(os.path.abspath(__file__))
SWATCH_DIR = os.path.join(HERE, "swatches")
OUT_JSON = os.path.join(HERE, "catalog_seed.json")
W, H = 600, 400  # swatch canvas size

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36")


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def make_grain_swatch(hexval, w=W, h=H):
    """Procedural wood-grain texture tinted to `hexval`.

    Streaks run horizontally (the way deck boards lie). This is only a
    stand-in so the picker and the Gemini pipeline have *something* to show;
    swap in a real swatch URL when you have one.
    """
    base = np.array(hex_to_rgb(hexval), dtype=float)
    x = np.linspace(0, 1, w)[None, :]
    y = np.linspace(0, 1, h)[:, None]
    # wavy horizontal grain lines + fine noise -> brightness multiplier
    streak = 0.10 * np.sin(2 * np.pi * (y * 16) + 1.8 * np.sin(2 * np.pi * x * 1.3))
    streak += 0.05 * np.sin(2 * np.pi * (y * 47) + 0.7)
    noise = np.random.normal(0, 0.025, (h, w))
    shade = 1.0 + streak + noise
    img = np.clip(base[None, None, :] * shade[:, :, None], 0, 255).astype("uint8")
    return Image.fromarray(img, "RGB")


def download_swatch(url):
    """Return a PIL image from a swatch URL, or None on failure.

    Trex images come off a Scene7 server ("/is/image/"); ?wid sizes them and
    we request JPG so files stay small. Other hosts (e.g. TimberTech's
    WordPress uploads, incl. .webp) are fetched as-is — PIL decodes them.
    """
    if "/is/image/" in url:
        sep = "&" if "?" in url else "?"
        candidates = [f"{url}{sep}wid={W}&fmt=jpg&qlt=85"]
    else:
        # try full-size first; fall back to the thumbnail if the sized
        # variant was the only real file (e.g. ...-150x150.webp)
        candidates = [url]
        import re as _re
        if not _re.search(r"-\d+x\d+\.(jpe?g|png|webp)$", url):
            candidates.append(_re.sub(r"\.(jpe?g|png|webp)$", r"-150x150.\1", url))
    for sized in candidates:
        for attempt in range(2):
            try:
                r = requests.get(sized, headers={"User-Agent": UA}, timeout=20)
                r.raise_for_status()
                return Image.open(io.BytesIO(r.content)).convert("RGB")
            except Exception as e:
                if attempt == 0:
                    time.sleep(1.0)
                    continue
                err = e.__class__.__name__
    print(f"    ! download failed ({err}); using placeholder")
    return None


def main():
    os.makedirs(SWATCH_DIR, exist_ok=True)
    records = catalog_source.build_records()
    seed = []
    n_real = n_ph = n_fallback = 0

    for i, rec in enumerate(records, 1):
        rid = rec["id"]
        img = None
        source = "generated_placeholder"
        ext = "png"

        if rec["swatch_url"]:
            img = download_swatch(rec["swatch_url"])
            if img is not None:
                source = "downloaded_real"
                ext = "jpg"
                n_real += 1
            else:
                n_fallback += 1  # had a URL but it failed -> placeholder

        if img is None:
            img = make_grain_swatch(rec["hex"])
            if not rec["swatch_url"]:
                n_ph += 1

        fname = f"{rid}.{ext}"
        fpath = os.path.join(SWATCH_DIR, fname)
        img.save(fpath, quality=88) if ext == "jpg" else img.save(fpath)

        out = dict(rec)
        out.pop("hex", None)  # hex was only needed to build placeholders
        out["swatch_source"] = source
        out["swatch_path"] = f"swatches/{fname}"
        out["swatch_w"], out["swatch_h"] = img.size
        seed.append(out)
        print(f"[{i:>2}/{len(records)}] {rid:<42} {source}")

    with open(OUT_JSON, "w") as f:
        json.dump(
            {"snapshot_date": catalog_source.SNAPSHOT_DATE,
             "count": len(seed),
             "materials": seed},
            f, indent=2,
        )

    print("\n" + "=" * 60)
    print(f"  Total materials      : {len(records)}")
    print(f"  Real swatches        : {n_real}")
    print(f"  Generated placeholders: {n_ph}")
    if n_fallback:
        print(f"  URL failed -> placeholder: {n_fallback}")
    print(f"  Wrote                : catalog_seed.json + swatches/")
    print("=" * 60)


if __name__ == "__main__":
    main()
