"""
catalog_source.py  —  SOURCE OF TRUTH for the deck-material catalog.

WHY THIS FILE EXISTS
--------------------
This is the *human-edited* part of the catalog. It holds the structure
(brand -> collection -> color) plus a one-line description and a color hex
for each material. A separate script (collect_catalog.py) reads this file,
downloads real swatch images where a URL is provided, generates a stand-in
swatch where one isn't, and writes the machine-readable catalog_seed.json.

So: edit THIS file by hand; never hand-edit the JSON. Re-run the collector
to rebuild. That separation is what makes the catalog "reproducible".

ROW FORMAT (one material = one row)
-----------------------------------
    (name, color_family, hex, swatch_url_or_None, description)

  - name          display label shown in the picker  ("Spiced Rum")
  - color_family  one of: brown / grey / neutral / red / dark  (powers a future "filter by tone")
  - hex           approximate color, used to TINT the placeholder swatch when no real image exists
  - swatch_url    real product swatch image URL, or None (None -> generate a placeholder)
  - description    one line, double-duty: shown to the homeowner AND fed into the Gemini prompt

Groups attach the shared fields (brand / collection / material_type) so we
don't repeat them on every row. The builder at the bottom expands rows into
full records and assigns a stable id like "trex-transcend-lineage-biscayne".

DATA CONFIDENCE
---------------
SNAPSHOT_DATE below is when this list was compiled. Color lineups change
yearly. The 7 Trex Lineage rows carry REAL swatch URLs (harvested from
trex.com on the snapshot date). Everything else uses placeholders for now;
color names/descriptions are a best-effort current snapshot to verify with
your distributor. Low-confidence rows are marked with a trailing comment.
"""

SNAPSHOT_DATE = "2026-06-29"

TREX_IMG = "https://images.trex.com/is/image/trexcompany/"

GROUPS = [
    # ---------------- TREX (composite) ----------------
    dict(brand="Trex", collection="Transcend Lineage", material_type="composite", rows=[
        ("Island Mist", "grey",    "#9a9a93", TREX_IMG+"lin-3inch-001-im-decking-sample-profile-IMTL35000", "Cool medley of calming silver-grey tones with a refined grain."),
        ("Rainier",     "grey",    "#a7a39b", TREX_IMG+"lin-3inch-001-rn-decking-sample-profile-RNTL35000", "Airy mountain grey with subtle silver tones and delicate grain."),
        ("Carmel",      "neutral", "#b3a48c", TREX_IMG+"lin-3inch-25151-cl-decking-sample-profile-CLTL35000", "Soft creamy taupe with toasty brown and grey undertones."),
        ("Biscayne",    "neutral", "#ab9a82", TREX_IMG+"lin-3inch-001-bc-decking-sample-profile-BCTL35000", "Warm taupe with subtle movement; Trex 2026 Color of the Year."),
        ("Jasper",      "brown",   "#5c4836", TREX_IMG+"lin-3inch-001-ja-decking-sample-profile-JATL35000", "Deep mocha with a rich umber hue and delicate streaking."),
        ("Salt Flat",   "grey",    "#b8b4ab", TREX_IMG+"lin-3inch-001-sf-decking-sample-profile-SFTL35000", "Natural symphony of silvers, whites and greys."),
        ("Hatteras",    "brown",   "#8f7a5f", TREX_IMG+"lin-3inch-001-ht-decking-sample-profile-HTTL35000", "Neutral windswept brown evoking surf and sand."),
    ]),
    dict(brand="Trex", collection="Transcend Earth Tones", material_type="composite", rows=[
        ("Spiced Rum",      "red",   "#6b4530", None, "Deep red-brown with subtle black streaking; tropical warmth."),
        ("Lava Rock",       "dark",  "#3f3b39", None, "Charcoal near-black with dark streaking."),
        ("Tiki Torch",      "brown", "#9c6b3b", None, "Warm honey brown with golden undertones."),
        ("Vintage Lantern", "red",   "#7a4332", None, "Red-brown with rustic, weathered character."),
        ("Rope Swing",      "brown", "#9c8567", None, "Medium tan-brown, soft and natural."),
    ]),
    dict(brand="Trex", collection="Transcend Tropicals", material_type="composite", rows=[
        ("Havana Gold", "brown", "#a9793f", None, "Golden tan with dramatic darker-brown streaking."),
        ("Tree House",  "brown", "#6f543b", None, "Rich variegated brown with multi-tonal grain."),
    ]),
    dict(brand="Trex", collection="Select", material_type="composite", rows=[
        ("Malted Barley", "brown",   "#8a7558", None, "Earthy browns and soft greys with milled-grain character."),
        ("Millstone",     "grey",    "#6f6c66", None, "Weathered grey with charcoal undertones."),
        ("Golden Hour",   "brown",   "#b08a55", None, "Sun-kissed golden hue with coconut-brown undertones."),
        ("Pebble Beach",  "grey",    "#a8a59d", None, "Light-toned weathered grey with natural wood grain."),
        ("Martis Valley", "neutral", "#c0ad8f", None, "Airy sunlit beige drifting between sand and sea-worn stone."),
        ("Saddle",        "brown",   "#7c5c3c", None, "Classic warm mid-brown."),  # legacy color, verify
        ("Pebble Grey",   "grey",    "#9b9890", None, "Soft neutral grey."),       # legacy color, verify
        ("Madeira",       "red",     "#5e4031", None, "Dark red-brown, rich and traditional."),  # legacy color, verify
    ]),
    dict(brand="Trex", collection="Enhance", material_type="composite", rows=[
        ("Beach Dune",   "neutral", "#b3a182", None, "Soft tan with a warm coastal feel."),
        ("Clam Shell",   "grey",    "#b7b4ac", None, "Light driftwood grey."),
        ("Toasted Sand", "neutral", "#c2b394", None, "Light sandy tan, clean and bright."),
        ("Foggy Wharf",  "grey",    "#807e78", None, "Medium muted grey."),
        ("Tide Pool",    "grey",    "#6d6a62", None, "Grey-brown with onyx-black streaks."),
        ("Saddle",       "brown",   "#7c5c3c", None, "Warm classic brown (Enhance line)."),
        ("Coastal Bluff","grey",    "#8f8c84", None, "Cool mid grey."),   # verify
        ("Rocky Harbor", "dark",    "#5f5a52", None, "Deep grey-brown."), # verify
    ]),
    dict(brand="Trex", collection="Signature", material_type="composite", rows=[
        ("Ocracoke", "dark", "#4a4642", None, "Deep charcoal-brown, premium matte look."),  # low confidence, verify
        ("Whidbey",  "grey", "#8e8b84", None, "Refined mid grey, premium line."),           # low confidence, verify
    ]),

    # ---------------- TIMBERTECH / AZEK (PVC) ----------------
    dict(brand="TimberTech", collection="AZEK Vintage", material_type="composite", rows=[
        ("Coastline",      "grey",  "#9a978e", None, "Soft weathered grey with subtle streaking (PVC)."),
        ("Weathered Teak", "brown", "#8a6f4e", None, "Warm medium brown with grey undertones (PVC)."),
        ("Dark Hickory",   "dark",  "#5a4636", None, "Deep brown with dramatic streaking (PVC)."),
        ("Mahogany",       "red",   "#6e3b2e", None, "Deep reddish-brown, hardwood look (PVC)."),
        ("English Walnut", "dark",  "#4f3a2a", None, "Rich deep brown with woodgrain detail (PVC)."),
    ]),
    dict(brand="TimberTech", collection="AZEK Landmark", material_type="composite", rows=[
        ("Castle Gate",      "grey",    "#6b6a66", None, "Grey-brown crosscut hardwood look (PVC)."),
        ("American Walnut",  "brown",   "#5d4634", None, "Warm walnut brown, hand-scraped (PVC)."),
        ("French White Oak", "neutral", "#b3a187", None, "Light oak tone with character grain (PVC)."),
        ("Boardwalk",        "neutral", "#8f8579", None, "Weathered grey-taupe (PVC)."),
    ]),
    dict(brand="TimberTech", collection="AZEK Harvest", material_type="composite", rows=[
        ("Brownstone", "brown", "#6f5642", None, "Traditional brown, cathedral grain (PVC)."),
        ("Slate Gray", "grey",  "#6d6d6b", None, "Solid contemporary grey (PVC)."),
        ("Kona",       "dark",  "#4a3a2c", None, "Deep espresso brown (PVC)."),
    ]),
    dict(brand="TimberTech", collection="AZEK Porch", material_type="composite", rows=[
        ("Oyster", "neutral", "#bdb6a6", None, "Light tongue-and-groove porch tone (PVC)."),  # Porch shares other colors; Oyster is unique
    ]),
    # ---------------- TIMBERTECH PRO (composite) ----------------
    dict(brand="TimberTech", collection="PRO Legacy", material_type="composite", rows=[
        ("Mocha",     "brown", "#5c4636", None, "Rich mocha brown, hand-scraped."),
        ("Ashwood",   "grey",  "#9a9388", None, "Soft grey-taupe with pigment blend."),
        ("Espresso",  "dark",  "#43342a", None, "Dark espresso brown."),
        ("Pecan",     "brown", "#7c5c3e", None, "Warm pecan brown."),
        ("Tigerwood", "red",   "#6e4327", None, "Reddish-brown with exotic streaking."),
    ]),
    dict(brand="TimberTech", collection="PRO Reserve", material_type="composite", rows=[
        ("Antique Leather", "brown", "#6b4a32", None, "Warm leathery brown, multi-tonal."),
        ("Dark Roast",      "dark",  "#4a3528", None, "Deep coffee brown."),
        ("Driftwood",       "grey",  "#8d8a82", None, "Weathered driftwood grey."),
    ]),
    dict(brand="TimberTech", collection="PRO Terrain", material_type="composite", rows=[
        ("Stony Gray",   "grey",  "#86847e", None, "Cost-conscious mid grey."),     # verify
        ("Brown Oak",    "brown", "#6f543c", None, "Traditional oak brown."),       # verify
        ("Silver Maple", "grey",  "#9b968b", None, "Light silvery grey."),          # verify
        ("Rustic Elm",   "brown", "#6e5b46", None, "Muted rustic brown."),          # verify
    ]),
    # ---------------- TIMBERTECH EDGE (composite, budget) ----------------
    dict(brand="TimberTech", collection="EDGE", material_type="composite", rows=[
        ("Sea Salt Gray", "grey",    "#a7a49c", None, "Breezy light grey, budget line."),
        ("Coconut Husk",  "neutral", "#8a6f4f", None, "Natural sandy brown, budget line."),
        ("Dark Teak",     "brown",   "#5e4632", None, "Rich medium brown, budget line."),
        ("Driftwood",     "grey",    "#8d8a82", None, "Cool-toned weathered grey, budget line."),
    ]),

    # ---------------- NATURAL WOOD SPECIES ----------------
    # No brand, no collection. One representative look each (v1: natural finish only).
    dict(brand=None, collection=None, material_type="wood", rows=[
        ("Redwood",                "red",   "#9a5a3c", None, "Natural redwood: warm reddish-brown, straight even grain."),
        ("Douglas Fir",            "neutral","#c39a63", None, "Natural Douglas fir: light amber-honey with prominent grain."),
        ("Ipe (Brazilian Walnut)", "dark",  "#5a4334", None, "Dense tropical hardwood: rich dark brown, fine tight grain."),
    ]),
]


def _slugify(text):
    out = []
    for ch in text.lower():
        if ch.isalnum():
            out.append(ch)
        elif out and out[-1] != "-":
            out.append("-")
    return "".join(out).strip("-")


def build_records():
    """Expand the compact GROUPS/rows into full catalog records."""
    records = []
    seen_ids = set()
    for g in GROUPS:
        brand = g["brand"]
        collection = g["collection"]
        mtype = g["material_type"]
        for (name, family, hexval, url, desc) in g["rows"]:
            if mtype == "wood":
                rid = "wood-" + _slugify(name)
            else:
                rid = _slugify(f"{brand}-{collection}-{name}")
            # de-dupe ids (e.g. "Saddle" / "Driftwood" appear in two collections)
            base_id = rid
            n = 2
            while rid in seen_ids:
                rid = f"{base_id}-{n}"
                n += 1
            seen_ids.add(rid)
            records.append({
                "id": rid,
                "material_type": mtype,
                "brand": brand,
                "collection": collection,
                "name": name,
                "color_family": family,
                "hex": hexval,
                "swatch_url": url,
                "description": desc,
            })
    return records


if __name__ == "__main__":
    recs = build_records()
    real = sum(1 for r in recs if r["swatch_url"])
    print(f"Snapshot {SNAPSHOT_DATE}: {len(recs)} records "
          f"({real} with real swatch URLs, {len(recs)-real} placeholder).")
