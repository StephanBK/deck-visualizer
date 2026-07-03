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
yearly. As of 2026-07-03 every composite row carries a REAL swatch URL
harvested from the live trex.com / timbertech.com product pages (rendered
in a browser — the swatch data is not in the static HTML). Colors that no
longer appear on the supplier pages were dropped (Trex: Vintage Lantern,
Tree House, Martis Valley, Madeira, Beach Dune, Coastal Bluff, all of
Signature; TimberTech: Stony Gray, Rustic Elm, Porch Oyster, EDGE
Driftwood), and the suppliers' new colors were added.
"""

SNAPSHOT_DATE = "2026-07-03"

TREX_IMG = "https://images.trex.com/is/image/trexcompany/"
TT_IMG = "https://shop.timbertech.com/wp-content/uploads/"

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
        ("Spiced Rum", "red",   "#6b4530", TREX_IMG+"trn-3inch-001-sr-decking-sample-profile-SRT35000", "Deep red-brown with subtle black streaking; tropical warmth."),
        ("Lava Rock",  "dark",  "#3f3b39", TREX_IMG+"trn-3inch-001-lr-decking-sample-profile-LRT35000", "Charcoal near-black with dark streaking."),
        ("Tiki Torch", "brown", "#9c6b3b", TREX_IMG+"trn-3inch-001-tt-decking-sample-profile-TTT35000", "Warm honey brown with golden undertones."),
        ("Rope Swing", "brown", "#9c8567", TREX_IMG+"trn-3inch-001-rs-decking-sample-profile-RST35000", "Medium tan-brown, soft and natural."),
    ]),
    dict(brand="Trex", collection="Transcend Tropicals", material_type="composite", rows=[
        ("Havana Gold", "brown", "#a9793f", TREX_IMG+"trn-3inch-001-hg-decking-sample-profile-HGT35000", "Golden tan with dramatic darker-brown streaking."),
    ]),
    dict(brand="Trex", collection="Select", material_type="composite", rows=[
        ("Malted Barley",  "brown", "#8a7558", TREX_IMG+"sel-3inch-001-my-decking-sample-profile-MYS235000", "Earthy browns and soft greys with milled-grain character."),
        ("Millstone",      "grey",  "#6f6c66", TREX_IMG+"sel-3inch-001-ms-decking-sample-profile-MS2S35000", "Weathered grey with charcoal undertones."),
        ("Pebble Grey",    "grey",  "#9b9890", TREX_IMG+"sel-3inch-001-pg-decking-sample-profile-PGS35000", "Soft neutral grey."),
        ("Saddle",         "brown", "#7c5c3c", TREX_IMG+"sel-3inch-001-sd-decking-sample-profile-SDS35000", "Classic warm mid-brown."),
        ("Whiskey Barrel", "dark",  "#5f4632", TREX_IMG+"sel-3inch-001-wl-decking-sample-profile-WLS235000", "Rich barrel brown with warm, char-kissed depth."),
    ]),
    dict(brand="Trex", collection="Enhance", material_type="composite", rows=[
        ("Foggy Wharf",   "grey",    "#807e78", TREX_IMG+"enh-3-inch-samples-24443-fw-decking-profile-FWE35000", "Medium muted grey."),
        ("Rocky Harbor",  "dark",    "#5f5a52", TREX_IMG+"enh-3-inch-samples-24447-rh-decking-profile-RHE35000", "Deep grey-brown."),
        ("Toasted Sand",  "neutral", "#c2b394", TREX_IMG+"enh-3-inch-samples-24455-ts-decking-profile-TTSE35000", "Toasty medium brown with sun-baked warmth."),
        ("Honey Grove",   "brown",   "#a97c46", TREX_IMG+"enh-3-inch-samples-24436-hy-decking-profile-HYE35000", "Light honeyed tan with soft, even grain."),
        ("Cinnamon Cove", "red",     "#8a5638", TREX_IMG+"enh-3-inch-samples-24459-cc-decking-profile-CCE35000", "Spiced cinnamon brown with reddish warmth."),
        ("Golden Hour",   "brown",   "#b08a55", TREX_IMG+"enh-3halfinch-002-gh-square-swatch", "Sun-kissed golden hue with coconut-brown undertones."),
        ("Tide Pool",     "grey",    "#6d6a62", TREX_IMG+"enh-3-inch-samples-24470-tp-decking-profile-TPE35000", "Light coastal grey with subtle warm undertones."),
        ("Clam Shell",    "grey",    "#b7b4ac", TREX_IMG+"enh-3-inch-samples-24474-cs-decking-profile-CSE35000", "Light driftwood grey."),
        ("Saddle",        "brown",   "#7c5c3c", TREX_IMG+"enh-3-inch-samples-24479-sd-decking-profile-SDE35000", "Warm classic brown (Enhance line)."),
        ("Pebble Beach",  "grey",    "#a8a59d", TREX_IMG+"enh-3halfinch-four-scallop-001-pb-grooved-decking-profile-PBE350000", "Light-toned weathered grey with natural wood grain."),
    ]),

    # ---------------- TIMBERTECH / AZEK (Advanced PVC) ----------------
    dict(brand="TimberTech", collection="AZEK Vintage", material_type="composite", rows=[
        ("Coastline",      "grey",  "#9a978e", TT_IMG+"2020/02/azek_vintage_coastline_displayswatch_cc-web.jpg", "Medium gray with warm tan and charcoal undertones; aged-hardwood look (PVC)."),
        ("Cypress",        "red",   "#7a4a33", TT_IMG+"2021/04/azek_vintage_cypress_displayswatch_cc-web-3.jpg", "Closely resembles ipe: tropical auburn-brown with mineral streaks (PVC)."),
        ("Weathered Teak", "brown", "#8a6f4e", TT_IMG+"2020/03/azek_vintage_weatheredteak_displayswatch_cc-web.jpg", "Warm medium brown with grey undertones (PVC)."),
        ("Dark Hickory",   "dark",  "#5a4636", TT_IMG+"2020/03/azek_vintage_darkhickory_displayswatch_cc-web-1.jpg", "Deep charcoal-brown with dramatic light streaks (PVC)."),
        ("Mahogany",       "red",   "#6e3b2e", TT_IMG+"2021/04/azek_vintage_mahogany_displayswatch_cc-web.jpg", "Rich russet mahogany, hardwood look (PVC)."),
        ("English Walnut", "dark",  "#4f3a2a", TT_IMG+"2020/03/azek_vintage_englishwalnut_displayswatch_cc-web.jpg", "Woodland-inspired warm walnut brown (PVC)."),
    ]),
    dict(brand="TimberTech", collection="AZEK Landmark", material_type="composite", rows=[
        ("Castle Gate",      "grey",    "#6b6a66", TT_IMG+"2021/02/Product-Swatch-AZEK-Landmark-TimberTech-CASTLEGATE-335.jpg", "Stormy grey with cool undertones; reclaimed-wood look (PVC)."),
        ("American Walnut",  "brown",   "#5d4634", TT_IMG+"2021/04/Product-Swatch-AZEK-Landmark-TimberTech-AMERICANWALNUT-326.jpg", "Deep cool brown, chocolate to ashy black (PVC)."),
        ("French White Oak", "neutral", "#b3a187", TT_IMG+"2021/02/Product-Swatch-AZEK-Landmark-TimberTech-FRENCHWHITEOAK-504.jpg", "Light organic oak with warm greys and tannins (PVC)."),
        ("Boardwalk",        "neutral", "#8f8579", TT_IMG+"2023/01/TimberTech-Boardwalk-Landmark-Advanced-PVC-Decking-Swatch-xs.jpg", "Light warm-grey, weathered coastal boardwalk feel (PVC)."),
    ]),
    dict(brand="TimberTech", collection="AZEK Harvest", material_type="composite", rows=[
        ("Brownstone", "brown", "#6f5642", TT_IMG+"2020/03/azek_brownstone_displayswatch_cc-web.jpg", "Sunny versatile light tan-brown (PVC)."),
        ("Slate Gray", "grey",  "#6d6d6b", TT_IMG+"2020/02/azek_harvest_slategray_displayswatch_cc-web.jpg", "Warm-toned light grey, highly versatile (PVC)."),
        ("Kona",       "dark",  "#4a3a2c", TT_IMG+"2020/03/azek_harvest_kona_displayswatch_cc-web.jpg", "Deep bold brown, great for contrast (PVC)."),
    ]),
    dict(brand="TimberTech", collection="AZEK Harvest Plus", material_type="composite", rows=[
        ("Timber Gray",   "grey",    "#8b8b87", TT_IMG+"2025/01/TimberTech-Advanced-PVC-Harvest-Plus-Timber-Gray-Decking-attribute-swatch.webp", "Balanced mid gray with soft grain (PVC)."),
        ("Toasted Wheat", "neutral", "#b99e6f", TT_IMG+"2025/01/TimberTech-Advanced-PVC-Harvest-Plus-Toasted-Wheat-Decking-attribute-swatch.webp", "Golden wheat tan, warm and sunny (PVC)."),
    ]),
    # ---------------- TIMBERTECH PRO (composite) ----------------
    dict(brand="TimberTech", collection="PRO Legacy", material_type="composite", rows=[
        ("Mocha",           "brown",   "#5c4636", TT_IMG+"2020/03/tt_legacy_mocha_displayswatch_cc-web.jpg", "Deeply saturated brown with cool undertones."),
        ("Ashwood",         "grey",    "#9a9388", TT_IMG+"2020/03/PRO-Legacy-Ashwood-Swatch.jpg", "Medium coastal grey with charcoal grain."),
        ("Espresso",        "dark",    "#43342a", TT_IMG+"2020/03/tt_legacy_espresso_displayswatch_cc-web-1.jpg", "Luxurious dark wood tone with a cool grey cast."),
        ("Pecan",           "brown",   "#7c5c3e", TT_IMG+"2020/03/tt_legacy_pecan_displayswatch_cc-web.jpg", "Classic medium pecan brown."),
        ("Tigerwood",       "red",     "#6e4327", TT_IMG+"2020/03/tt_legacy_tigerwood_displayswatch_cc-web.jpg", "Exotic streaking from subtle tans to rich browns."),
        ("Whitewash Cedar", "neutral", "#b8ab97", TT_IMG+"2020/03/tt_legacy_whitewashcedar_displayswatch_cc-web.jpg", "Light whitewashed cedar look with soft grain."),
    ]),
    dict(brand="TimberTech", collection="PRO Reserve", material_type="composite", rows=[
        ("Antique Leather",    "brown", "#6b4a32", TT_IMG+"2020/04/tt-pro-reserve-antique-leather-display-swatch-500x500-300x300-1.jpg", "Warm leathery brown, multi-tonal."),
        ("Dark Roast",         "dark",  "#4a3528", TT_IMG+"2020/03/timbertech-pro-reserve-darkroast-displayswatch-500x500-1.jpg", "Deep coffee brown."),
        ("Driftwood",          "grey",  "#8d8a82", TT_IMG+"2020/03/tt-pro-reserve-driftwood-display-swatch-500x500-1.jpg", "Weathered driftwood grey."),
        ("Reclaimed Chestnut", "brown", "#7a5a3e", TT_IMG+"2023/01/Timbertech-Reclaimed-Chestnut-Reserve-Composite-Decking-Swatch-xs.jpg", "Reclaimed chestnut brown with rustic character."),
    ]),
    dict(brand="TimberTech", collection="PRO Terrain", material_type="composite", rows=[
        ("Brown Oak",    "brown", "#6f543c", TT_IMG+"2020/03/tt_terrain_brownoak_displayswatch_cc-web.jpg", "Traditional oak brown."),
        ("Silver Maple", "grey",  "#9b968b", TT_IMG+"2020/03/tt_terrain_silvermaple_displaysw.jpg", "Light silvery grey."),
    ]),
    dict(brand="TimberTech", collection="Terrain Plus", material_type="composite", rows=[
        ("Dark Oak",          "dark",    "#55412f", TT_IMG+"2024/01/timbertech-terrain-plus-collection-dark-oak-composite-decking-board-swatch-icon.jpg", "Deep stained-oak brown."),
        ("Natural White Oak", "neutral", "#b7a685", TT_IMG+"2024/01/timbertech-terrain-plus-collection-natural-white-oak-composite-decking-board-swatch-icon.jpg", "Light natural white oak."),
        ("Weathered Oak",     "grey",    "#94897a", TT_IMG+"2024/01/timbertech-terrain-plus-collection-weathered-oak-composite-decking-board-swatch-icon.jpg", "Softly weathered grey-brown oak."),
    ]),
    dict(brand="TimberTech", collection="Premier Plus", material_type="composite", rows=[
        ("Natural Oak", "neutral", "#b3925f", TT_IMG+"2025/05/natural-oak-swatch.webp", "Warm natural oak tone."),
    ]),
    # ---------------- TIMBERTECH EDGE (composite, budget) ----------------
    dict(brand="TimberTech", collection="EDGE Prime Plus", material_type="composite", rows=[
        ("Sea Salt Gray", "grey",    "#a7a49c", TT_IMG+"2020/03/timbertech-edge-seasaltgray-displayswatch-500x500-1.jpg", "Breezy light grey, budget-friendly."),
        ("Coconut Husk",  "neutral", "#8a6f4f", TT_IMG+"2020/03/timbertech-edge-coconuthusk-displayswatch-500x500-1.jpg", "Natural sandy brown, budget-friendly."),
        ("Dark Cocoa",    "dark",    "#4c382b", TT_IMG+"2021/11/TimberTech-Dark-Cocoa-Prime-Plus-Collection-EDGE-Decking-Swatch.jpg", "Deep cocoa brown, budget-friendly."),
    ]),
    dict(brand="TimberTech", collection="EDGE Premier", material_type="composite", rows=[
        ("Dark Teak",     "brown", "#5e4632", TT_IMG+"2020/03/edge-darkteak_displayswatch_opt.jpg", "Rich medium teak brown, budget-friendly."),
        ("Maritime Gray", "grey",  "#8e8c86", TT_IMG+"2020/06/EDGE-MaritimeGray-Swatch-8288.jpg", "Cool maritime grey, budget-friendly."),
    ]),

    # ---------------- NATURAL WOOD SPECIES ----------------
    # No brand, no collection. One representative look each (v1: natural finish only).
    dict(brand=None, collection=None, material_type="wood", rows=[
        # Redwood: no freely-licensed real board photo found; still a generated stand-in.
        # Best fix: photograph a real redwood sample board and drop it in.
        ("Redwood",                "red",   "#9a5a3c", None, "Natural redwood: warm reddish-brown, straight even grain."),
        # Wikimedia "WoodDeck-4180" (CC BY-SA 3.0, David R. Tribble) — representative amber decking close-up.
        ("Douglas Fir",            "neutral","#c39a63", "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d0/WoodDeck-4180.jpg/960px-WoodDeck-4180.jpg", "Natural Douglas fir: light amber-honey with prominent grain."),
        # Wikimedia "Ipe deck stain" (public domain) — real oiled ipe deck.
        ("Ipe (Brazilian Walnut)", "dark",  "#5a4334", "https://upload.wikimedia.org/wikipedia/commons/c/c4/Ipe_deck_stain.jpg", "Dense tropical hardwood: rich dark brown, fine tight grain."),
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
