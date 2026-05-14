# HCAS Hub

The central HCAS student super-app.
**Tagline:** *Everything HCAS, one tap.*

One mobile-first PWA with five tabs:
- **Today** — verdict card + assignments + team events a]t a glance
- **Lunch** — menu + crowd ratings + verdict (eat / your call / order Uber Eats)
- **Work** — your assignments
- **Teams** — HCAS athletics: today, upcoming, last result
- **Notes** — type a topic, AI streams organized study notes

---

## Run it

```bash
cd hcas-hub
pip install -r requirements.txt
export GOOGLE_API_KEY=AIzaSyAQ2JIBRV7eF7kOTgkIPwUa9ixC9NmKfcQ             # only needed for the Notes tab (Gemini)
uvicorn main:app --reload
```

Open <http://127.0.0.1:8000>.

The app is mobile-first. To get the best demo:
1. Find your laptop's IP (`ipconfig getifaddr en0` on Mac).
2. On your phone, open `http://<that-ip>:8000`.
3. iOS: Share → **Add to Home Screen**. Android: menu → **Install app**.
4. The Hub now opens as a real app icon, fullscreen.

---

## Get an API key for the Notes tab

1. Go to <https://aistudio.google.com/app/apikey> and click **Create API key** (Gemini, free tier).
2. Copy the key.
3. `export GOOGLE_API_KEY=AIzaSyAQ2JIBRV7eF7kOTgkIPwUa9ixC9NmKfcQ` (or put it in a `.env` and `source` it before `uvicorn`)
4. Restart the server.

Without the key, the rest of the app still works — Notes shows a friendly fallback message.

### Want to refresh the lunch menu next month?

```bash
python scripts/fetch_menu.py            # downloads the latest PDF
python scripts/fetch_menu.py --parse    # also auto-parses with Claude vision (needs ANTHROPIC_API_KEY)
```

---

## Microsoft Teams Sync (Chrome extension)

Pulls each student's own Teams assignments straight from the browser into the Hub's calendar — no school IT approval, no Azure setup, no OAuth. Each student logs into Teams in Chrome themselves; the extension scrapes the visible Assignments page and POSTs it to the local Hub backend.

### Install (once, ~1 minute)

1. Open **chrome://extensions** in Chrome.
2. Toggle **Developer mode** on (top right).
3. Click **Load unpacked**.
4. Pick the `extension/` folder inside `hcas-hub/`.
5. Pin the extension so its icon is visible in the toolbar.

### Use

1. In Chrome, sign in to <https://teams.microsoft.com> with your school account.
2. Click **Assignments** in Teams' left rail.
3. Either click the floating **SYNC TO HCAS HUB** badge in the bottom-right of the Teams page, **or** click the extension icon → **Sync now**.
4. Open the Hub's [Calendar](http://127.0.0.1:8000/calendar) — your assignments appear, marked with a small **T** badge.

### How it works (and what it doesn't do)

- The content script reads only the DOM you can already see. It does **not** read your auth tokens, does **not** make API calls to Microsoft on your behalf, and does **not** send anything anywhere except the URL configured in the popup (default `http://127.0.0.1:8000`).
- The data layer dedupes by `(source, external_id)` so re-syncing the same Teams page only updates titles/dates — no duplicates.
- DOM selectors will drift over time as Microsoft updates Teams. If sync stops finding rows, the relevant code is `extension/content.js → scrapeAssignments()`.

### Future upgrade — real Microsoft Graph API

If/when HCAS IT approves an Azure AD app, the import endpoint (`/api/import_assignments`) accepts the same JSON shape Microsoft Graph's `/education/me/assignments` returns. You can swap the extension for a server-side Graph poll without changing any UI code.

---

## Demo script (Presentation Day)

1. Open the Hub on a phone, mirrored to the projector.
2. **Today screen** — "everything I need before first period."
3. Tap the lunch card. Today is *Pizza Day*: **EAT THE LUNCH** (4.3★ from 187 students).
4. In the day picker, tap **Tuesday**. *Tuna Surprise*: **ORDER UBER** (1.8★).
5. Tap **Open Uber Eats** — opens the real Uber Eats site, delivery to HCAS prefilled.
6. **Work tab** — add an assignment, drag-completed look.
7. **Teams tab** — today's games + last result.
8. **Notes tab** — type *photosynthesis stages* → notes stream in.

---

## Project layout

```
hcas-hub/
├── main.py                 # FastAPI app + all routes
├── lib/
│   ├── lunch_verdict.py    # the IP — pure verdict logic with self-tests
│   ├── db.py               # SQLite for ratings + assignments
│   ├── seed.py             # static HCAS data loader
│   └── claude.py           # Anthropic SDK wrapper for Notes
├── templates/
│   ├── base.html           # shared shell + bottom nav + PWA hooks
│   ├── today.html
│   ├── lunch.html
│   ├── assignments.html
│   ├── teams.html
│   └── notes.html
├── static/
│   ├── sw.js               # PWA service worker (offline cache)
│   ├── icon-192.png
│   └── icon-512.png
├── prompts/
│   └── notes_system.md     # study-notes prompt — edit to tune note quality
├── data/
│   ├── hcas_seed.json      # menu, teams, demo assignments
│   └── hub.db              # created on first run
└── requirements.txt
```

---

## What's the verdict logic?

`lib/lunch_verdict.py`:
- < 2.5★ → **ORDER UBER**
- 2.5★ ≤ x < 3.5★ → **YOUR CALL**
- ≥ 3.5★ → **EAT THE LUNCH**
- < 5 ratings → **YOUR CALL** (not enough data yet)

Run `python lib/lunch_verdict.py` to execute the boundary tests.

---

## Cuts (intentionally NOT built)

- PowerSchool / Canvas / Google Classroom integration
- Native iOS / Android apps (PWA is enough)
- Login (single-user demo for the capstone; pilot adds Supabase magic-link)
- Real Uber Eats API (deep links only)
- Multi-school / district admin
- Push notifications

---

## Pricing pitch (for Slide 9)

White-label per school. **$1/student/year.**
HCAS pilot → templated for any high school in the country.
