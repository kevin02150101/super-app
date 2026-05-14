"""下載前端離線資源到 app/static/ (一次性)。

執行:  python scripts/download_assets.py

下載完成後,Flask 應用即不再依賴任何 CDN。
"""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "app" / "static"
JS = STATIC / "js"
CSS = STATIC / "css"
JS.mkdir(parents=True, exist_ok=True)
CSS.mkdir(parents=True, exist_ok=True)

ASSETS = [
    # (輸出路徑, 來源 URL)
    (CSS / "bootstrap.min.css",
     "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"),
    (JS / "bootstrap.bundle.min.js",
     "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"),
    (JS / "react.production.min.js",
     "https://cdn.jsdelivr.net/npm/react@18.3.1/umd/react.production.min.js"),
    (JS / "react-dom.production.min.js",
     "https://cdn.jsdelivr.net/npm/react-dom@18.3.1/umd/react-dom.production.min.js"),
    (JS / "babel.min.js",
     "https://cdn.jsdelivr.net/npm/@babel/standalone@7.25.6/babel.min.js"),
    (JS / "axios.min.js",
     "https://cdn.jsdelivr.net/npm/axios@1.7.7/dist/axios.min.js"),
]


def download(dst: Path, url: str) -> None:
    if dst.exists() and dst.stat().st_size > 0:
        print(f"[skip] {dst.relative_to(ROOT)} 已存在")
        return
    print(f"[get ] {url} -> {dst.relative_to(ROOT)}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
    dst.write_bytes(data)
    print(f"       {len(data):,} bytes")


def main() -> int:
    print(f"目標目錄: {STATIC}")
    for dst, url in ASSETS:
        try:
            download(dst, url)
        except Exception as e:
            print(f"[fail] {url}: {e}", file=sys.stderr)
            return 1
    print("完成。所有前端資源皆已下載到本機,系統已脫離 CDN 依賴。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
