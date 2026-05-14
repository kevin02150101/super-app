"""下載前端離線資源到 app/static/vendor/。

執行方式::

    python scripts/download_assets.py

下載內容:
- Bootstrap 5.3 (CSS + bundle JS)
- Vue 3 (global production build)
- Axios (UMD min)
- SweetAlert2 (CSS + min JS)
"""
from __future__ import annotations

import os
import ssl
import sys
from pathlib import Path
from urllib.request import urlopen

try:
    import certifi
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CTX = ssl.create_default_context()

BASE = Path(__file__).resolve().parent.parent / "app" / "static" / "vendor"

ASSETS = {
    "bootstrap-5.3/bootstrap.min.css":
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css",
    "bootstrap-5.3/bootstrap.bundle.min.js":
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js",
    "vue-3/vue.global.prod.js":
        "https://cdn.jsdelivr.net/npm/vue@3.4.27/dist/vue.global.prod.js",
    "axios/axios.min.js":
        "https://cdn.jsdelivr.net/npm/axios@1.7.2/dist/axios.min.js",
    "sweetalert2/sweetalert2.min.css":
        "https://cdn.jsdelivr.net/npm/sweetalert2@11.12.0/dist/sweetalert2.min.css",
    "sweetalert2/sweetalert2.min.js":
        "https://cdn.jsdelivr.net/npm/sweetalert2@11.12.0/dist/sweetalert2.all.min.js",
}


def main() -> int:
    BASE.mkdir(parents=True, exist_ok=True)
    for rel, url in ASSETS.items():
        target = BASE / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.stat().st_size > 0:
            print(f"✔ 已存在:{rel}")
            continue
        print(f"⬇ 下載 {rel} ← {url}")
        try:
            with urlopen(url, context=_SSL_CTX, timeout=30) as resp:
                target.write_bytes(resp.read())
        except Exception as exc:  # noqa: BLE001
            print(f"✘ 失敗:{rel} — {exc}")
            return 1
    print("✅ 完成,所有資源已放置於 app/static/vendor/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
