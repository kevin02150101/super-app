# Publishing the Toolbox apps

Three apps need to leave localhost: **MyCam** (Flask), **BookFinder** (Flask + Playwright), **VibeSpec** (Vite/React).

Recommended hosts (free tiers):

| App         | Host                | Why                                            |
|-------------|---------------------|------------------------------------------------|
| MyCam       | Render (Python)     | Free Python web service, gunicorn              |
| BookFinder  | Render (Docker)     | Playwright needs Chromium → use Docker image   |
| VibeSpec    | Vercel              | Static SPA, instant CDN                        |

All manifests are already committed to this repo.

---

## 1 · Push the repo

```bash
cd "/Users/zhangruifeng/Desktop/super app"
git add -A
git commit -m "Add deploy manifests + HCAS theme for toolbox apps"
git push
```

---

## 2 · Deploy MyCam + BookFinder via Render Blueprint

1. Go to <https://dashboard.render.com/blueprints>
2. Click **New Blueprint Instance** → connect `kevin02150101/super-app`
3. Render reads [render.yaml](render.yaml) and offers to create `mycam` + `bookfinder`
4. For **mycam**, set the secret env var `GOOGLE_API_KEY` in the dashboard (value: same Gemini key from `hcas-hub/.env`)
5. Click **Apply**. Build logs stream in the dashboard.

URLs will be:
- `https://mycam.onrender.com`
- `https://bookfinder.onrender.com`

> Free tier spins down after 15 min of inactivity → first request after a nap takes ~30 s to wake up.
> BookFinder image is ~1 GB (Chromium) — first build is slow but cached after.

---

## 3 · Deploy VibeSpec via Vercel

```bash
cd vibespec-generator
npx vercel --prod
```

Or via the dashboard:
1. <https://vercel.com/new> → Import `kevin02150101/super-app`
2. **Root Directory** = `vibespec-generator`
3. Framework preset = **Vite** (auto-detected from [vercel.json](vibespec-generator/vercel.json))
4. Add env var `GEMINI_API_KEY` (value: same Gemini key)
5. Deploy

URL will be: `https://<your-project>.vercel.app`

> ⚠️ VibeSpec embeds the Gemini key into the JS bundle at build time (see
> [vibespec-generator/vite.config.ts](vibespec-generator/vite.config.ts)).
> Anyone who views the page can extract it. For public deploys, either
> (a) move the Gemini call to a serverless function, or
> (b) restrict the key to your Vercel domain in Google Cloud Console.

---

## 4 · Point the HCAS Hub Toolbox at the live URLs

Once deployed, set these env vars wherever `hcas-hub` runs:

```bash
export HCAS_TOOL_MYCAM_URL="https://mycam.onrender.com"
export HCAS_TOOL_BOOK_URL="https://bookfinder.onrender.com"
export HCAS_TOOL_VIBESPEC_URL="https://<your-vercel-project>.vercel.app"
```

The toolbox page will:
- replace the `:port` line with the live hostname
- hide the **Start** button (no local launch needed)
- show a green **Live** status

If a var is unset, that tool keeps its original local-launch behavior.

---

## Files added/changed

- [render.yaml](render.yaml) — Render Blueprint (MyCam + BookFinder)
- [book/Dockerfile](book/Dockerfile) — Playwright base image
- [book/.dockerignore](book/.dockerignore)
- [vibespec-generator/vercel.json](vibespec-generator/vercel.json)
- [hcas-hub/lib/toolbox.py](hcas-hub/lib/toolbox.py) — remote URL support
- [hcas-hub/main.py](hcas-hub/main.py) — pass `remote` flag to template
- [hcas-hub/templates/toolbox.html](hcas-hub/templates/toolbox.html) — Live pill, hide Start when remote
