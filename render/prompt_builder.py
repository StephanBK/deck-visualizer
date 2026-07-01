"""
prompt_builder.py  —  turns a chosen material into a Gemini instruction.

THE CORE IDEA (from the build plan):
  The salesperson never types a description. They pick a material; the code
  looks up that material's record in catalog_seed.json, grabs its name +
  description + swatch image, and fills in a fixed instruction template.

  The template spends as many words on what to KEEP as on what to CHANGE.
  That "keep unchanged" list is what stops the model from quietly redrawing
  railings, furniture, or the whole perspective.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG_DIR = os.path.normpath(os.path.join(HERE, "..", "catalog"))
SEED_PATH = os.path.join(CATALOG_DIR, "catalog_seed.json")


def load_catalog():
    with open(SEED_PATH) as f:
        return json.load(f)["materials"]


def get_material(material_id, catalog=None):
    catalog = catalog or load_catalog()
    for m in catalog:
        if m["id"] == material_id:
            return m
    raise KeyError(f"material id not found: {material_id!r}")


def swatch_abs_path(material):
    """Absolute path to this material's swatch image on disk."""
    return os.path.join(CATALOG_DIR, material["swatch_path"])


# The fill-in-the-blank template. {name} and {description} get replaced.
INSTRUCTION_TEMPLATE = (
    "You are editing the FIRST image: a real photograph of an existing outdoor deck. "
    "Your task is a MATERIAL SWAP that must be clearly visible. Resurface EVERY deck "
    "floor board so it takes on the decking material shown in the SECOND image — "
    "{name}: {description}. The boards' color, tone, and wood-grain finish must fully "
    "match the sample, completely replacing their current appearance. Match the "
    "sample's color precisely, even if it is much darker or lighter than the current "
    "boards — do NOT preserve the original deck color. "
    "Apply it across the entire deck surface, following the existing board direction, "
    "perspective, and lighting so it reads as real installed decking. "
    "Everything that is NOT the deck floor must stay EXACTLY as in the original: "
    "railings, posts, stairs, furniture, umbrellas, planters, plants, the house, "
    "fence, background, any people, and the overall lighting and camera angle. "
    "Do not add, remove, move, or resize any object. Only the deck boards change."
)


def build_instruction(material):
    return INSTRUCTION_TEMPLATE.format(
        name=material["name"],
        description=material["description"].rstrip("."),
    )


if __name__ == "__main__":
    # quick demo: show the instruction for a couple of materials
    for mid in ("trex-transcend-lineage-biscayne", "wood-ipe-brazilian-walnut"):
        m = get_material(mid)
        print(f"\n=== {m['name']} ({m['swatch_source']}) ===")
        print(build_instruction(m))
