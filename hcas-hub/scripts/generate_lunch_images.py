"""Generate a hero image for every school-lunch day using Gemini (Nano Banana).

Usage:
    export GEMINI_API_KEY=your_key_here   # or GOOGLE_API_KEY
    python scripts/generate_lunch_images.py            # only missing days
    python scripts/generate_lunch_images.py --force    # regenerate all
    python scripts/generate_lunch_images.py --day 2026-05-04

Output: static/lunch/<YYYY-MM-DD>.png
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import google.generativeai as genai

BASE = Path(__file__).resolve().parent.parent
SEED_PATH = BASE / "data" / "hcas_seed.json"
OUT_DIR = BASE / "static" / "lunch"

MODEL_NAME = "gemini-2.5-flash-image"  # Nano Banana


def build_prompt(menu: dict) -> str:
    headline = menu.get("headline") or "School lunch"
    main_dish = menu.get("main_dish") or ""
    items = [
        f"- {it.get('name', '')}".strip()
        for it in menu.get("items", [])
        if it.get("name")
    ]
    items_block = "\n".join(items) if items else ""
    return (
        "Generate a single appetizing overhead photograph of a school lunch tray. "
        "Style: warm natural lighting, shallow depth of field, clean wooden table, "
        "no text, no logos, no people, no hands. "
        "Square 1:1 framing. Realistic food photography.\n\n"
        f"Headline dish: {headline}\n"
        f"Main: {main_dish}\n"
        f"Items on the tray:\n{items_block}"
    )


def extract_image_bytes(resp) -> bytes | None:
    for cand in getattr(resp, "candidates", []) or []:
        content = getattr(cand, "content", None)
        if not content:
            continue
        for part in getattr(content, "parts", []) or []:
            inline = getattr(part, "inline_data", None)
            if inline and getattr(inline, "data", None):
                return inline.data
    return None


def generate_one(model, day: str, menu: dict, out_path: Path) -> bool:
    prompt = build_prompt(menu)
    resp = model.generate_content(prompt)
    img_bytes = extract_image_bytes(resp)
    if not img_bytes:
        print(f"  [{day}] no image returned", file=sys.stderr)
        return False
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(img_bytes)
    print(f"  [{day}] wrote {out_path.relative_to(BASE)} ({len(img_bytes)} bytes)")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true",
                    help="regenerate even if file exists")
    ap.add_argument("--day", help="only generate this YYYY-MM-DD")
    args = ap.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: set GEMINI_API_KEY (or GOOGLE_API_KEY)", file=sys.stderr)
        return 2
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_NAME)

    seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    menus: dict = seed.get("lunch_menus", {})

    days = [args.day] if args.day else sorted(menus.keys())
    ok = fail = skipped = 0
    for day in days:
        menu = menus.get(day)
        if not menu:
            print(f"  [{day}] not in seed, skipping", file=sys.stderr)
            continue
        if menu.get("is_holiday"):
            print(f"  [{day}] holiday, skipping")
            skipped += 1
            continue
        out_path = OUT_DIR / f"{day}.png"
        if out_path.exists() and not args.force:
            print(f"  [{day}] exists, skipping (use --force to regenerate)")
            skipped += 1
            continue
        try:
            if generate_one(model, day, menu, out_path):
                ok += 1
            else:
                fail += 1
        except Exception as e:  # noqa: BLE001
            print(f"  [{day}] error: {e}", file=sys.stderr)
            fail += 1

    print(f"\nDone. ok={ok} fail={fail} skipped={skipped}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
