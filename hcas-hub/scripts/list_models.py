"""List Gemini models available with your GOOGLE_API_KEY.

Run this when generateContent says 'model not found' to see what your key can use.

    GOOGLE_API_KEY=AIza... python scripts/list_models.py
"""
import os
import sys
import google.generativeai as genai

key = os.environ.get("GOOGLE_API_KEY")
if not key:
    sys.exit("GOOGLE_API_KEY not set. Run: GOOGLE_API_KEY=AIza... python scripts/list_models.py")

genai.configure(api_key=key)

print(f"{'name':<55} {'methods'}")
print("-" * 95)
gen_models = []
for m in genai.list_models():
    methods = ",".join(m.supported_generation_methods)
    print(f"{m.name:<55} {methods}")
    if "generateContent" in m.supported_generation_methods:
        gen_models.append(m.name)

print()
print(f"{len(gen_models)} model(s) support generateContent.")
if gen_models:
    print()
    print("→ Suggested MODEL_CANDIDATES for lib/claude.py (in preferred order):")
    flash = [n.replace("models/", "") for n in gen_models if "flash" in n.lower()]
    rest  = [n.replace("models/", "") for n in gen_models if "flash" not in n.lower()]
    for n in flash[:3] + rest[:2]:
        print(f"    {n!r},")
