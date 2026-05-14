"""Toolbox launcher — start side-project dev servers as subprocesses.

Each tool is registered with the working directory, the command to run, and
the TCP port it listens on. ``status`` does a non-blocking TCP probe; ``launch``
spawns the command detached and never blocks the request.

Stdout/stderr of launched tools is redirected to ``hcas-hub/logs/<key>.log``.
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# hcas-hub/ → parent → super app/
HUB_DIR = Path(__file__).resolve().parent.parent
ROOT = HUB_DIR.parent
LOG_DIR = HUB_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)


def _venv_python(project: Path) -> str:
    """Return the project's venv python if present, else the current one."""
    candidate = project / ".venv" / "bin" / "python"
    if candidate.exists():
        return str(candidate)
    return sys.executable


@dataclass
class Tool:
    key: str
    name: str
    tagline: str
    description: str
    stack: str
    badge: str
    port: int
    cwd: Path
    # Command builder — receives the resolved cwd, returns argv list.
    build_cmd: callable = field(repr=False)
    env: dict = field(default_factory=dict)

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def cmd(self) -> list[str]:
        return self.build_cmd(self.cwd)


TOOLS: dict[str, Tool] = {
    "mycam": Tool(
        key="mycam",
        name="MyCam",
        tagline="AI Food Image Analysis",
        description=(
            "Snap or upload a photo — Gemini identifies the food, estimates "
            "calories, and builds a hero dashboard with your eating history."
        ),
        stack="Flask · Gemini · Vue 3 · Chart.js",
        badge="AI · Vision",
        port=5001,
        cwd=ROOT / "calories" / "MyCam",
        build_cmd=lambda p: [_venv_python(p), "run.py"],
        env={"PORT": "5001"},
    ),
    "book": Tool(
        key="book",
        name="BookFinder",
        tagline="Books.com.tw search engine",
        description=(
            "Search books on Books.com.tw via Playwright scraping. Card-based "
            "results with KPI dashboards, hot keywords, publishers, and "
            "14-day trends."
        ),
        stack="Flask · React · Playwright · SQLite",
        badge="Search · Data",
        port=5002,
        cwd=ROOT / "book",
        build_cmd=lambda p: [_venv_python(p), "run.py"],
        env={"PORT": "5002"},
    ),
    "vibespec": Tool(
        key="vibespec",
        name="VibeSpec Generator",
        tagline="AI spec drafting studio",
        description=(
            "Generate product spec drafts in seconds with an AI Studio–powered "
            "Vite + React workflow. Bring your Gemini API key and ship docs "
            "faster."
        ),
        stack="Vite · React · TypeScript · Gemini",
        badge="AI · Docs",
        port=5179,
        cwd=ROOT / "vibespec-generator",
        build_cmd=lambda p: [
            "npm", "run", "dev", "--",
            "--port", "5179", "--strictPort", "--host", "127.0.0.1",
        ],
    ),
}


def is_running(port: int, host: str = "127.0.0.1", timeout: float = 0.25) -> bool:
    """Return True if something is listening on ``host:port``."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def status(tool: Tool) -> dict:
    return {
        "key": tool.key,
        "running": is_running(tool.port),
        "url": tool.url,
    }


def launch(tool: Tool) -> dict:
    """Start the tool's dev server if it isn't already up. Non-blocking."""
    if is_running(tool.port):
        return {"key": tool.key, "running": True, "url": tool.url, "started": False}

    if not tool.cwd.exists():
        return {
            "key": tool.key,
            "running": False,
            "url": tool.url,
            "started": False,
            "error": f"Project directory missing: {tool.cwd}",
        }

    log_path = LOG_DIR / f"{tool.key}.log"
    env = {**os.environ, **tool.env}
    # Stream logs to disk; detach so the child outlives this request.
    log_fh = open(log_path, "ab", buffering=0)
    try:
        subprocess.Popen(  # noqa: S603 — argv is built from our trusted registry
            tool.cmd(),
            cwd=str(tool.cwd),
            env=env,
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    except FileNotFoundError as exc:
        log_fh.close()
        return {
            "key": tool.key,
            "running": False,
            "url": tool.url,
            "started": False,
            "error": f"Command not found: {exc}",
        }
    except OSError as exc:
        log_fh.close()
        return {
            "key": tool.key,
            "running": False,
            "url": tool.url,
            "started": False,
            "error": str(exc),
        }

    return {
        "key": tool.key,
        "running": False,  # not listening yet; client polls /toolbox/status
        "url": tool.url,
        "started": True,
        "log": str(log_path.relative_to(HUB_DIR)),
    }
