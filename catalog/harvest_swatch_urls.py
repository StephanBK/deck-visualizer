"""
harvest_swatch_urls.py  —  pull real swatch image URLs from a supplier page.

This is the tool that makes real-image coverage reproducible. The supplier
swatch URLs are NOT guessable (e.g. Trex's "Carmel" uses a different code than
its siblings), so we read them off the live product page instead.

USAGE:
    python3 harvest_swatch_urls.py "https://www.trex.com/products/decking/lineage/"

It prints every distinct swatch-style image URL it finds. Copy the right ones
into the matching rows in catalog_source.py, then re-run collect_catalog.py.

Proven working for Trex product pages. Other suppliers may need the regex
pattern below adjusted (printed URLs let you eyeball what the site uses).
"""

import re
import sys
import requests

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36")

# Trex swatch images look like .../trexcompany/<something>-decking-sample-profile-<CODE>
PATTERNS = [
    r"images\.trex\.com/is/image/trexcompany/[^\"'\\ ]*sample-profile-[A-Z0-9]+",
]


def harvest(url):
    html = requests.get(url, headers={"User-Agent": UA}, timeout=20).text
    found = set()
    for pat in PATTERNS:
        for m in re.findall(pat, html):
            found.add("https://" + m.split(":")[0] if not m.startswith("http") else m)
    return sorted(found)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python3 harvest_swatch_urls.py <product_page_url>")
        sys.exit(1)
    urls = harvest(sys.argv[1])
    if not urls:
        print("No swatch URLs matched. Inspect the page HTML and adjust PATTERNS.")
    for u in urls:
        print(u)
