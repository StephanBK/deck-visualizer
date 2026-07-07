"""
prompt_builder.py  —  turns a chosen material + options into a Gemini instruction.

THE CORE IDEA (from the build plan):
  The salesperson never types a description. They pick a material; the code
  looks up that material's record in catalog_seed.json, grabs its name +
  description + swatch image, and fills in a fixed instruction template.

  The template spends as many words on what to KEEP as on what to CHANGE.
  That "keep unchanged" list is what stops the model from quietly redrawing
  railings, furniture, or the whole perspective.

MODES:
  resurface  — swap only the deck floor boards (most reliable).
  replace    — rebuild the whole deck structure (boards, railings, stairs)
               in the new material.
  build_new  — the photo has no deck; construct one where it plausibly fits.

TOGGLES (composable with any mode):
  declutter        — remove loose clutter, keep permanent fixtures.
  stage_furniture  — add tasteful modern outdoor furniture.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG_DIR = os.path.normpath(os.path.join(HERE, "..", "catalog"))
SEED_PATH = os.path.join(CATALOG_DIR, "catalog_seed.json")

MODES = ("resurface", "replace", "build_new")


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


# --- what to CHANGE, per mode ({name}/{description} get filled in) -----------

MODE_TEMPLATES = {
    "resurface": (
        "You are editing the FIRST image: a real photograph of an existing outdoor deck. "
        "Your task is a MATERIAL SWAP that must be clearly visible. Resurface EVERY deck "
        "floor board so it takes on the decking material shown in the SECOND image — "
        "{name}: {description}. The boards' color, tone, and wood-grain finish must fully "
        "match the sample, completely replacing their current appearance. Match the "
        "sample's color precisely, even if it is much darker or lighter than the current "
        "boards — do NOT preserve the original deck color. "
        "Apply it across the entire deck surface, following the existing board direction, "
        "perspective, and lighting so it reads as real installed decking."
    ),
    "replace": (
        "You are editing the FIRST image: a real photograph of an existing outdoor deck. "
        "Your task is a FULL DECK REPLACEMENT that must be clearly visible. Rebuild the "
        "entire deck structure — floor boards, railings, posts, balusters, stairs, and "
        "fascia — as a brand-new deck made of the decking material shown in the SECOND "
        "image — {name}: {description}. Use a clean, modern railing design that "
        "coordinates with the new material. The new deck must occupy the same footprint, "
        "height, and orientation as the original, and match the photo's perspective and "
        "lighting so it reads as a real, professionally built installation. Match the "
        "sample's color precisely — do NOT preserve the original deck's color or style."
    ),
    "build_new": (
        "You are editing the FIRST image: a real photograph of a home's outdoor space "
        "that has no deck (or only a bare patch, lawn, or old patio where one could go). "
        "Your task is to CONSTRUCT A NEW DECK as a concept rendering. Design and add a "
        "realistic, professionally built deck made of the decking material shown in the "
        "SECOND image — {name}: {description} — placed where a deck most plausibly fits "
        "(typically attached to the house, replacing the bare/underused area). Size and "
        "proportion it sensibly for the space, include simple coordinated railings if "
        "the height calls for them, and match the photo's perspective, sunlight, and "
        "shadows so it reads as if it were really there."
    ),
}

# --- what to KEEP, per mode ---------------------------------------------------
# Assembled separately so the toggles below can relax it without contradiction.

KEEP_LISTS = {
    "resurface": (
        "Everything that is NOT the deck floor must stay EXACTLY as in the original: "
        "railings, posts, stairs, {things}, the house, fence, background, any people, "
        "and the overall lighting and camera angle."
    ),
    "replace": (
        "Everything that is NOT the deck structure must stay EXACTLY as in the "
        "original: {things}, the house, fence, yard, background, any people, and the "
        "overall lighting and camera angle."
    ),
    "build_new": (
        "Everything else must stay EXACTLY as in the original: {things}, the house and "
        "its doors/windows, fence, background, any people, and the overall "
        "lighting and camera angle."
    ),
}

# Objects normally protected by the keep-list. Staging/decluttering may remove
# or add such objects, so the wording adapts to the toggles.
KEEP_THINGS = "furniture, umbrellas, planters, plants"

STRICT_CLAUSE = "Do not add, remove, move, or resize any object."

DECLUTTER_CLAUSE = (
    "Also DECLUTTER the space: remove loose clutter such as hoses, toys, tarps, "
    "bins, tools, cushions in disarray, and stray debris. Keep permanent fixtures "
    "(built-in seating, grills, large planters, lighting) in place."
)

STAGE_CLAUSE = (
    "Also STAGE the finished deck with tasteful, modern outdoor furniture "
    "appropriate to its size — for example a lounge or dining set and a couple of "
    "planters — arranged naturally, as a professional stager would."
)

# Appended server-side to EVERY render instruction. Invisible to the app —
# a tuned quality floor so results look like photographs, not renderings.
QUALITY_CLAUSE = (
    "QUALITY REQUIREMENTS: The result must be indistinguishable from a real "
    "photograph. Deck boards must have realistic width (about 14 cm / 5.5 in), "
    "visible seams and end-gaps, and subtle natural grain variation between "
    "boards — never a repeating texture. Preserve the original photo's camera "
    "angle, focal length, resolution, sharpness, white balance, lighting "
    "direction, and shadows exactly. Straight edges must stay perfectly "
    "straight — no warping, bowing, or perspective drift. Keep colors natural "
    "and true to the material sample; no oversaturated, glossy, or cartoonish "
    "rendering."
)

FUSION_QUALITY_CLAUSE = (
    "The image must read as a professional architectural photograph: realistic "
    "board scale and seams, natural color grading, straight lines kept straight, "
    "no cartoonish saturation."
)


def build_instruction(material, mode="resurface", declutter=False, stage_furniture=False):
    """Full Gemini instruction for one render: mode template + keep-list + toggles."""
    if mode not in MODES:
        raise ValueError(f"unknown mode: {mode!r} (expected one of {MODES})")

    change = MODE_TEMPLATES[mode].format(
        name=material["name"],
        description=material["description"].rstrip("."),
    )

    # If staging or decluttering, furniture/planters are fair game — drop them
    # from the keep-list so the instruction doesn't contradict itself.
    things = KEEP_THINGS if not (declutter or stage_furniture) else "plants"
    keep = KEEP_LISTS[mode].format(things=things)

    parts = [change, keep]
    if declutter:
        parts.append(DECLUTTER_CLAUSE)
    if stage_furniture:
        parts.append(STAGE_CLAUSE)
    if not declutter and not stage_furniture:
        parts.append(STRICT_CLAUSE)
    parts.append(QUALITY_CLAUSE)
    return " ".join(parts)


def build_fusion_instruction(material=None):
    """Instruction for the 'fusion hero shot': one polished marketing render
    combined from already-rendered result image(s). Clearly a rendering, so it
    may relight and restage — but the material and architecture must not drift."""
    material_note = (
        f"The decking material is {material['name']} "
        f"({material['description'].rstrip('.')}); its color, tone, and grain must "
        "stay exactly as shown. "
        if material else
        "The decking material's color, tone, and grain must stay exactly as shown. "
    )
    return (
        "The attached image(s) show a finished deck project (AI renderings of the "
        "same deck). Produce ONE polished marketing hero image of this deck: warm "
        "golden-hour lighting, gently staged with tasteful modern outdoor furniture, "
        "clean composition with subtle depth, photorealistic quality. "
        + material_note +
        "Keep the deck's structure, the house, and all architecture identical to the "
        "source image(s) — this is a beauty shot of the SAME project, not a new design. "
        + FUSION_QUALITY_CLAUSE
    )


if __name__ == "__main__":
    # quick demo: one material through every mode, plus toggles and the hero shot
    m = get_material("trex-transcend-lineage-biscayne")
    for mode in MODES:
        print(f"\n=== {mode} ===")
        print(build_instruction(m, mode=mode))
    print("\n=== resurface + declutter + stage ===")
    print(build_instruction(m, declutter=True, stage_furniture=True))
    print("\n=== fusion hero ===")
    print(build_fusion_instruction(m))
