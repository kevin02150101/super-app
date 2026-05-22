"""Thin wrapper around the Google Gemini SDK for the Notes generator."""
import os
from pathlib import Path
import google.generativeai as genai

NOTES_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "notes_system.md"
# Models to try, in order. Google retires old ones; we try a current name first
# and fall back to older names if the API rejects them.
MODEL_CANDIDATES = [
    "gemini-2.5-flash-preview-05-20",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash",
]


def _resolve_model(system_instruction: str):
    """Return the first GenerativeModel whose name the API accepts."""
    last_err = None
    for name in MODEL_CANDIDATES:
        try:
            m = genai.GenerativeModel(name, system_instruction=system_instruction)
            # Cheap probe: ask the API to count tokens; this surfaces 404s before streaming
            m.count_tokens("ping")
            return m, name
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"No usable Gemini model found. Last error: {last_err}")


# Mime types Gemini reliably accepts inline (≤ ~20MB per file).
ALLOWED_MIMES = {
    "application/pdf",
    "image/jpeg", "image/jpg", "image/png", "image/webp", "image/heic", "image/heif",
    "text/plain", "text/markdown", "text/csv",
}
# Hard cap so we don't blow up the request body.
MAX_FILE_BYTES = 18 * 1024 * 1024  # 18 MB inline limit (Gemini accepts ~20MB)


def stream_notes(topic: str, attachments: list[dict] | None = None):
    """Yield chunks of generated notes.

    Args:
        topic: free-text topic or question. May be empty if attachments are given.
        attachments: optional list of {"mime": str, "data": bytes, "name": str}.
            Each file is sent as inline data to the multimodal model.
    """
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    system = NOTES_PROMPT_PATH.read_text()
    model, _name = _resolve_model(system)

    parts: list = []
    attachments = attachments or []
    if attachments:
        names = ", ".join(a.get("name") or "file" for a in attachments)
        header = f"Attached file(s): {names}."
        if topic:
            parts.append(f"{header}\nTopic / question: {topic}\n\nUse the attached files as the primary source. Extract the key ideas and produce study notes per the system format.")
        else:
            parts.append(f"{header}\n\nAnalyze the attached files and produce study notes per the system format. If the content is a homework problem, explain how to solve it instead of giving only the answer.")
        for a in attachments:
            parts.append({"mime_type": a["mime"], "data": a["data"]})
    else:
        parts.append(f"Topic: {topic}")

    response = model.generate_content(
        parts,
        generation_config={"max_output_tokens": 4096},
        stream=True,
    )
    for chunk in response:
        if chunk.text:
            yield chunk.text
