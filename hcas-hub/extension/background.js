// HCAS Hub — Teams Sync background service worker.
// Receives scraped assignment lists from the content script and forwards
// them to the local HCAS Hub backend. The Hub URL is configurable via the
// popup (default http://127.0.0.1:8000).

const DEFAULT_HUB_URL = "http://127.0.0.1:8000";

async function getHubUrl() {
  const { hubUrl } = await chrome.storage.sync.get({ hubUrl: DEFAULT_HUB_URL });
  return (hubUrl || DEFAULT_HUB_URL).replace(/\/$/, "");
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg && msg.type === "IMPORT_ASSIGNMENTS") {
    (async () => {
      try {
        const hub = await getHubUrl();
        const res = await fetch(`${hub}/api/import_assignments`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ rows: msg.rows }),
        });
        if (!res.ok) {
          const text = await res.text();
          sendResponse({ ok: false, error: `HTTP ${res.status}: ${text.slice(0, 80)}` });
          return;
        }
        const data = await res.json();
        sendResponse({ ok: true, ...data });
      } catch (err) {
        sendResponse({ ok: false, error: String(err) });
      }
    })();
    return true; // async sendResponse
  }
  if (msg && msg.type === "IMPORT_SCHEDULE") {
    (async () => {
      try {
        const hub = await getHubUrl();
        const res = await fetch(`${hub}/api/import_schedule`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ rows: msg.rows, replace: !!msg.replace }),
        });
        if (!res.ok) {
          const text = await res.text();
          sendResponse({ ok: false, error: `HTTP ${res.status}: ${text.slice(0, 80)}` });
          return;
        }
        const data = await res.json();
        sendResponse({ ok: true, ...data });
      } catch (err) {
        sendResponse({ ok: false, error: String(err) });
      }
    })();
    return true;
  }
});
