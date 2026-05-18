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


def stream_notes(topic: str):
    """Yield chunks of generated notes for a topic. Caller renders as they arrive."""
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    system = NOTES_PROMPT_PATH.read_text()
    model, _name = _resolve_model(system)
    response = model.generate_content(
        f"Topic: {topic}",
        generation_config={"max_output_tokens": 4096},
        stream=True,
    )
    for chunk in response:
        if chunk.text:
            yield chunk.text
