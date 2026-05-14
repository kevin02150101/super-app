"""Fetch the latest HCAS lunch & snack menu PDF.

Usage:
    python scripts/fetch_menu.py            # downloads the latest PDF found on the page
    python scripts/fetch_menu.py --parse    # also calls Claude vision to update hcas_seed.json (needs ANTHROPIC_API_KEY)

This is meant to be run once a month when the new menu posts.
"""
import argparse
import os
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

import urllib.request

PAGE_URL = "https://www.hcas.tw/school-lunch/"
DATA_DIR = Path(__file__).parent.parent / "data"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (HCAS-Hub menu fetcher)"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def find_latest_pdf() -> str:
    """Scan the school-lunch page HTML for the most recent LunchSnackMenu PDF link."""
    html = fetch(PAGE_URL).decode("utf-8", errors="ignore")
    # Match every PDF URL on the page
    urls = re.findall(r'https?://[^"\'<> ]+\.pdf', html)
    # Prefer ones that look like the lunch+snack menu
    menu_urls = [u for u in urls if "Lunch" in u or "Snack" in u or "menu" in u.lower()]
    if not menu_urls:
        menu_urls = urls
    if not menu_urls:
        raise SystemExit("No PDF links found on the school-lunch page — site layout may have changed.")
    # Pick the lexicographically last (the most recent month is usually the last by upload date)
    return sorted(menu_urls)[-1]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--parse", action="store_true", help="Also auto-parse with Claude vision (needs ANTHROPIC_API_KEY)")
    args = p.parse_args()

    DATA_DIR.mkdir(exist_ok=True)
    print(f"→ Reading {PAGE_URL}")
    pdf_url = find_latest_pdf()
    print(f"→ Latest menu PDF: {pdf_url}")
    out = DATA_DIR / Path(pdf_url).name
    out.write_bytes(fetch(pdf_url))
    print(f"✓ Saved to {out}  ({out.stat().st_size//1024} KB)")

    if not args.parse:
        print("\nNext step:")
        print("  Open the PDF and update data/hcas_seed.json with the new month's menu.")
        print("  Or run: python scripts/fetch_menu.py --parse  (auto-extracts with Claude vision).")
        return

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("--parse needs ANTHROPIC_API_KEY in env")

    print("\n→ Asking Claude to extract the menu as JSON...")
    import base64, json
    from anthropic import Anthropic

    pdf_b64 = base64.standard_b64encode(out.read_bytes()).decode("ascii")

    client = Anthropic()
    prompt = """Extract every lunch day from this school menu PDF as JSON. Schema:

{
  "lunch_menus": {
    "YYYY-MM-DD": {
      "headline": "<short main-dish English name>",
      "icon": "<emoji>",
      "main_dish": "<Chinese · English of the carb base, e.g. '白飯 · White Rice'>",
      "items": [
        {"name": "<English>", "name_zh": "<Chinese>", "station": "<Dish 1|Dish 2|Dish 3|Dish 4|Soup|Snack>", "allergens": ["egg"|"dairy"|"seafood"|"nut"|"gluten"|"soy"]}
      ],
      "allergens": [<union of all item allergens>],
      "prior_avg_rating": <reasonable guess 2.0-4.9>,
      "prior_rating_count": <reasonable 50-200>
    }
  }
}

Rules:
- Dates use the year shown in the PDF header (115年 = 2026 in ROC calendar terms; the English header gives the Gregorian month/year).
- For Labor Day or holidays: set "is_holiday": true, "items": [], rating null/0.
- Output ONLY valid JSON, no commentary, no markdown fences."""

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        messages=[{
            "role": "user",
            "content": [
                {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_b64}},
                {"type": "text", "text": prompt},
            ],
        }],
    )
    text = resp.content[0].text.strip()
    # Strip optional ```json fences
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()

    try:
        new_menus = json.loads(text)["lunch_menus"]
    except Exception as e:
        sys.exit(f"Couldn't parse Claude's JSON: {e}\n\nRaw output:\n{text[:1000]}")

    seed_path = DATA_DIR / "hcas_seed.json"
    seed = json.loads(seed_path.read_text())
    seed["lunch_menus"].update(new_menus)
    seed_path.write_text(json.dumps(seed, indent=2, ensure_ascii=False))
    print(f"✓ Merged {len(new_menus)} new menu days into {seed_path.name}")
    for d in sorted(new_menus.keys())[:5]:
        print(f"   · {d}: {new_menus[d].get('headline')}")
    if len(new_menus) > 5:
        print(f"   · …and {len(new_menus) - 5} more")


if __name__ == "__main__":
    main()
