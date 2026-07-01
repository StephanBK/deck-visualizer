"""
try_one.py  —  test the render in isolation (Step 2 deliverable).

USAGE:
    export GEMINI_API_KEY="your_key"
    python3 try_one.py path/to/deck_photo.jpg trex-transcend-lineage-biscayne

It looks up the material, builds the instruction, calls Gemini once, and saves:
    outputs/<deck>__<material>__after.jpg          the edited image
    outputs/<deck>__<material>__before_after.jpg   side-by-side for easy eyeballing

The whole app is built around RETRY, not one-shot perfection: if a result nudges
something it shouldn't, just run the same command again for a fresh take (~5 sec).

List available material ids:
    python3 try_one.py --list
"""

import os
import sys

from PIL import Image

import prompt_builder as pb
from gemini_edit import edit_deck_photo, GeminiError

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")


def list_materials():
    for m in pb.load_catalog():
        tag = "REAL " if m["swatch_source"] == "downloaded_real" else "(ph) "
        brand = m["brand"] or "Natural wood"
        print(f"  {tag}{m['id']:<44} {brand} / {m['name']}")


def side_by_side(before_path, after_img):
    before = Image.open(before_path).convert("RGB")
    h = 600
    bw = int(before.width * h / before.height)
    aw = int(after_img.width * h / after_img.height)
    before = before.resize((bw, h))
    after = after_img.resize((aw, h))
    canvas = Image.new("RGB", (bw + aw + 20, h), "white")
    canvas.paste(before, (0, 0))
    canvas.paste(after, (bw + 20, 0))
    return canvas


def main(argv):
    if not argv or argv[0] in ("--list", "-l"):
        list_materials()
        return
    if len(argv) < 2:
        print("usage: python3 try_one.py <deck_photo> <material_id>   (or --list)")
        return

    deck_path, material_id = argv[0], argv[1]
    if not os.path.exists(deck_path):
        print(f"deck photo not found: {deck_path}")
        return

    os.makedirs(OUT, exist_ok=True)
    material = pb.get_material(material_id)
    swatch = pb.swatch_abs_path(material)
    instruction = pb.build_instruction(material)

    print(f"Material : {material['brand'] or 'Wood'} / {material['name']} "
          f"({material['swatch_source']})")
    print(f"Deck     : {deck_path}")
    print("Calling Gemini ...")

    try:
        result = edit_deck_photo(deck_path, swatch, instruction)
    except GeminiError as e:
        print(f"\nFAILED: {e}")
        return

    stem = f"{os.path.splitext(os.path.basename(deck_path))[0]}__{material_id}"
    after_path = os.path.join(OUT, f"{stem}__after.jpg")
    combo_path = os.path.join(OUT, f"{stem}__before_after.jpg")
    result.save(after_path, quality=90)
    side_by_side(deck_path, result).save(combo_path, quality=90)
    print(f"\nSaved:\n  {after_path}\n  {combo_path}")
    print("Tip: run the same command again for a fresh take if this one nudged something.")


if __name__ == "__main__":
    main(sys.argv[1:])
