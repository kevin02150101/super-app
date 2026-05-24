// HCAS Hub — Teams Sync content script.
//
// Runs on teams.microsoft.com / teams.cloud.microsoft. When the user is on
// the Assignments page, reads the visible assignment rows from the DOM and
// lets them ship the list to the local HCAS Hub backend with one click.
//
// We don't grab tokens, we don't read other students' data, we don't post
// anywhere except the URL the user configured (default http://127.0.0.1:8000).

(() => {
  if (window.__hcasHubSyncLoaded) return;
  window.__hcasHubSyncLoaded = true;

  const STATE = { lastFound: 0 };
  const log = (...a) => console.debug("[HCAS Hub]", ...a);

  // The Assignments app lives in an iframe at assignments.edu.cloud.microsoft.
  // The parent Teams shell page has no assignment DOM, so skip it.
  // We require BOTH: hostname matches assignments.edu.cloud.microsoft AND we're
  // not the top frame (defense-in-depth).
  const isAssignmentsFrame =
    /^assignments\.edu\.cloud\.microsoft$/i.test(location.hostname) &&
    window !== window.top;
  log("frame check", { host: location.hostname, isAssignmentsFrame, isTop: window === window.top });
  if (!isAssignmentsFrame) {
    // Still register a no-op listener so the popup gets a clean response if it asks the top frame.
    chrome.runtime.onMessage.addListener((msg, _s, sendResponse) => {
      if (msg && (msg.type === "PEEK_ROWS" || msg.type === "PEEK")) {
        sendResponse({ ok: true, rows: [], found: 0, note: "wrong frame" });
      } else if (msg && msg.type === "TRIGGER_SYNC") {
        sendResponse({ ok: false, error: "Not on the assignments frame" });
      }
    });
    return;
  }

  // ─── DOM scraper ──────────────────────────────────────────────────────
  // The Teams Assignments page has changed format a few times. Currently
  // (May 2026 layout) it groups items under date headers like:
  //   "May 15th  Friday"
  //   ┌──────────────────────────────────┐
  //   │ Storage Tank Expo                 │
  //   │ Due at 8:00 AM                    │
  //   │ Pre-AP Geometry with Statistics   │
  //   │                       10 points   │
  //   └──────────────────────────────────┘
  //
  // We:
  //   1. Walk the document for every text node that says "Due at HH:MM AM/PM"
  //   2. Climb to the nearest enclosing card-ish container
  //   3. Pull the title (first non-empty line that isn't "Due at…" or class)
  //   4. Pull the class (line right after the "Due at" line)
  //   5. Find the most recent date header before the card to compute due_at
  //   6. external_id = the link href if present, else a stable hash

  const MONTHS = {
    january:0,february:1,march:2,april:3,may:4,june:5,
    july:6,august:7,september:8,october:9,november:10,december:11,
    jan:0,feb:1,mar:2,apr:3,jun:5,jul:6,aug:7,sep:8,sept:8,oct:9,nov:10,dec:11,
  };

  function parseDateHeader(text) {
    // Examples:  "May 15th",  "May 15", "Friday May 15", "May 15th Friday"
    const m = text.match(/\b([A-Z][a-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?\b/);
    if (!m) return null;
    const month = MONTHS[m[1].toLowerCase()];
    if (month === undefined) return null;
    const day = parseInt(m[2], 10);
    const year = new Date().getFullYear();
    // Bias forward: if the month/day is more than 30 days behind today, assume next year
    const cand = new Date(year, month, day);
    const today = new Date();
    if ((today - cand) / (1000*60*60*24) > 30) cand.setFullYear(year + 1);
    return cand;
  }

  function parseTime(text) {
    // "Due at 8:00 AM" / "Due at 11:59 PM"
    const m = text.match(/Due\s+at\s+(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?/);
    if (!m) return null;
    let h = parseInt(m[1], 10);
    const min = parseInt(m[2], 10);
    const ap = (m[3] || "").toUpperCase();
    if (ap === "PM" && h < 12) h += 12;
    if (ap === "AM" && h === 12) h = 0;
    return { h, min };
  }

  // Walk all text nodes once and capture date-header positions
  function findDateHeaders() {
    const out = [];
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode())) {
      const t = (node.nodeValue || "").trim();
      if (!t || t.length > 60) continue;
      // Only match short header-shaped strings, e.g. "May 15th Friday"
      if (!/\b\d{1,2}(?:st|nd|rd|th)\b/.test(t) && !/^\w+ \d{1,2}$/.test(t)) continue;
      const d = parseDateHeader(t);
      if (!d) continue;
      // Only keep header-y elements (not body text)
      const el = node.parentElement;
      if (!el) continue;
      const tag = el.tagName.toLowerCase();
      const isHeader =
        /^h[1-6]$/.test(tag) ||
        el.getAttribute("role") === "heading" ||
        el.matches('[class*="header" i],[class*="date" i],[data-tid*="date" i]');
      if (!isHeader && t.length > 25) continue;
      out.push({ date: d, el });
    }
    return out;
  }

  // For an element, find the date header that comes BEFORE it in document order
  function nearestPriorDate(headers, el) {
    let best = null;
    for (const h of headers) {
      if (h.el.compareDocumentPosition(el) & Node.DOCUMENT_POSITION_FOLLOWING) {
        best = h.date;
      } else {
        break;
      }
    }
    return best;
  }

  function climbToCard(el) {
    let cur = el;
    for (let i = 0; i < 8 && cur; i++) {
      const role = cur.getAttribute && cur.getAttribute("role");
      const tid  = cur.getAttribute && cur.getAttribute("data-tid");
      if (
        cur.tagName === "LI" ||
        cur.tagName === "ARTICLE" ||
        role === "listitem" || role === "row" || role === "button" || role === "link" ||
        (tid && /assignment/i.test(tid))
      ) return cur;
      cur = cur.parentElement;
    }
    return el.parentElement || el;
  }

  // Scrape using the actual Fluent UI selectors from the Teams Assignments app.
  function scrapeAssignments() {
    const headers = findDateHeaders();
    const cards = document.querySelectorAll('[data-test="assignment-card"]');
    log("scrapeAssignments: found", cards.length, "card(s)");

    const rows = [];
    for (const card of cards) {
      const titleEl   = card.querySelector('[data-test="assignment-card-title-all-up-view"]');
      const subjectEl = card.querySelector('[data-testid="card-classOrModuleName"]');
      const title   = (titleEl?.textContent || "").trim().slice(0, 200);
      const subject = (subjectEl?.textContent || "").trim().slice(0, 80);
      if (!title) continue;

      // "Due at HH:MM AM/PM" lives in a presentation div under CardHeader__description
      const cardText = card.innerText || "";
      const time = parseTime(cardText);   // tolerant regex inside parseTime

      const date = nearestPriorDate(headers, card);
      let due_at = "";
      if (date && time) {
        const dt = new Date(date);
        dt.setHours(time.h, time.min, 0, 0);
        due_at = dt.toISOString();
      } else if (date) {
        const dt = new Date(date);
        dt.setHours(23, 59, 0, 0);
        due_at = dt.toISOString();
      }

      // Stable external id: derive from title+subject+due so re-syncs update,
      // not duplicate. The React-generated `card.id` is regenerated each
      // session and can't be trusted.
      const external_id = `teams::${title}::${subject}::${due_at}`;
      rows.push({ title, subject, due_at, external_id, source: "teams" });
    }

    // De-dup within this batch
    const map = new Map();
    for (const r of rows) map.set(r.external_id, r);
    return Array.from(map.values());
  }

  // ─── Floating sync badge ───────────────────────────────────────────────
  const BADGE_POS_KEY = "hcasBadgePos";

  function ensureBadge() {
    let badge = document.getElementById("hcas-hub-sync-badge");
    if (!badge) {
      badge = document.createElement("div");
      badge.id = "hcas-hub-sync-badge";
      Object.assign(badge.style, {
        position: "fixed", right: "16px", bottom: "16px", left: "auto", top: "auto",
        zIndex: 999999,
        background: "#0F1A2F", color: "#F5F7FA",
        font: '700 12px/1.2 -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, sans-serif',
        padding: "10px 14px 10px 28px",
        border: "1px solid rgba(59,207,255,0.25)",
        borderRadius: "8px", cursor: "grab",
        boxShadow: "0 6px 20px rgba(15,26,47,0.45), 0 0 0 1px rgba(30,150,229,0.15)",
        letterSpacing: "0.10em", textTransform: "uppercase", userSelect: "none",
        touchAction: "none",
      });
      badge.title = "Drag to move · Click to sync visible assignments to HCAS Hub";

      // Drag handle (left dotted grip)
      const grip = document.createElement("span");
      Object.assign(grip.style, {
        position: "absolute", left: "8px", top: "50%", transform: "translateY(-50%)",
        width: "8px", height: "14px", display: "inline-block",
        backgroundImage:
          "radial-gradient(circle, rgba(245,247,250,0.65) 1px, transparent 1.2px)",
        backgroundSize: "4px 4px",
        backgroundPosition: "0 0",
      });
      badge.appendChild(grip);

      const label = document.createElement("span");
      label.id = "hcas-hub-sync-badge-label";
      badge.appendChild(label);

      // Restore saved position
      try {
        chrome.storage.local.get(BADGE_POS_KEY, (data) => {
          const pos = data && data[BADGE_POS_KEY];
          if (pos && typeof pos.left === "number" && typeof pos.top === "number") {
            applyPosition(badge, pos.left, pos.top);
          }
        });
      } catch {}

      attachDrag(badge);

      // Click to sync — but only if it wasn't a drag
      badge.addEventListener("click", (e) => {
        if (badge.dataset.dragged === "1") {
          badge.dataset.dragged = "0";
          return;
        }
        sync();
      });

      document.body.appendChild(badge);
    }
    const label = badge.querySelector("#hcas-hub-sync-badge-label");
    if (label) label.textContent = `Sync to HCAS Hub${STATE.lastFound ? ` · ${STATE.lastFound} found` : ""}`;
  }

  function applyPosition(badge, left, top) {
    // Clamp to viewport
    const w = badge.offsetWidth || 200;
    const h = badge.offsetHeight || 40;
    left = Math.max(4, Math.min(left, window.innerWidth - w - 4));
    top  = Math.max(4, Math.min(top,  window.innerHeight - h - 4));
    badge.style.left = left + "px";
    badge.style.top = top + "px";
    badge.style.right = "auto";
    badge.style.bottom = "auto";
  }

  function attachDrag(badge) {
    let startX = 0, startY = 0, origLeft = 0, origTop = 0, moved = 0, dragging = false;

    function onDown(ev) {
      ev.preventDefault();
      dragging = true;
      moved = 0;
      badge.dataset.dragged = "0";
      badge.style.cursor = "grabbing";
      const rect = badge.getBoundingClientRect();
      origLeft = rect.left;
      origTop = rect.top;
      const p = ev.touches ? ev.touches[0] : ev;
      startX = p.clientX;
      startY = p.clientY;
      document.addEventListener("mousemove", onMove);
      document.addEventListener("mouseup", onUp);
      document.addEventListener("touchmove", onMove, { passive: false });
      document.addEventListener("touchend", onUp);
    }
    function onMove(ev) {
      if (!dragging) return;
      ev.preventDefault();
      const p = ev.touches ? ev.touches[0] : ev;
      const dx = p.clientX - startX;
      const dy = p.clientY - startY;
      moved = Math.max(moved, Math.abs(dx) + Math.abs(dy));
      applyPosition(badge, origLeft + dx, origTop + dy);
    }
    function onUp() {
      if (!dragging) return;
      dragging = false;
      badge.style.cursor = "grab";
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
      document.removeEventListener("touchmove", onMove);
      document.removeEventListener("touchend", onUp);
      if (moved > 4) {
        badge.dataset.dragged = "1";
        try {
          const rect = badge.getBoundingClientRect();
          chrome.storage.local.set({ [BADGE_POS_KEY]: { left: rect.left, top: rect.top } });
        } catch {}
      }
    }
    badge.addEventListener("mousedown", onDown);
    badge.addEventListener("touchstart", onDown, { passive: false });
  }

  function isContextValid() {
    try { return !!(chrome && chrome.runtime && chrome.runtime.id); }
    catch { return false; }
  }

  function sync() {
    return new Promise((resolve) => {
      if (!isContextValid()) {
        log("sync skipped — extension context invalidated. Reload the page.");
        resolve({ ok: false, error: "Extension reloaded. Refresh this Teams tab." });
        return;
      }
      const badge = document.getElementById("hcas-hub-sync-badge");
      const rows = scrapeAssignments();
      STATE.lastFound = rows.length;
      log("syncing", rows);
      if (badge) badge.textContent = `Syncing ${rows.length}…`;

      try {
        chrome.runtime.sendMessage({ type: "IMPORT_ASSIGNMENTS", rows }, (resp) => {
        if (badge) {
          if (resp && resp.ok) {
            badge.textContent = `Synced · +${resp.added} new, ${resp.updated} updated`;
            badge.style.background = "rgba(110,204,113,0.18)";
            badge.style.borderColor = "rgba(110,204,113,0.55)";
            badge.style.color = "#6ECC71";
          } else {
            badge.textContent = `Sync failed · ${resp ? resp.error : "no response"}`;
            badge.style.background = "rgba(255,64,64,0.18)";
            badge.style.borderColor = "rgba(255,64,64,0.55)";
            badge.style.color = "#FF4040";
          }
          setTimeout(() => {
            badge.style.background = "#0F1A2F";
            badge.style.borderColor = "rgba(59,207,255,0.25)";
            badge.style.color = "#F5F7FA";
            ensureBadge();
          }, 4000);
        }
        resolve(resp || { ok: false, error: "no response" });
      });
      } catch (err) {
        log("sync failed: " + err.message);
        resolve({ ok: false, error: err.message });
      }
    });
  }

  function tick() {
    if (!isContextValid()) {
      // Extension was reloaded — stop ticking, leave the stale badge in place.
      clearInterval(tickHandle);
      return;
    }
    STATE.lastFound = scrapeAssignments().length;
    ensureBadge();
  }
  const tickHandle = setInterval(tick, 2500);
  tick();

  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg && msg.type === "TRIGGER_SYNC") {
      sync().then((resp) => sendResponse(resp));
      return true; // async
    }
    if (msg && msg.type === "PEEK") {
      sendResponse({ ok: true, found: scrapeAssignments().length });
      return false;
    }
    if (msg && msg.type === "PEEK_ROWS") {
      sendResponse({ ok: true, rows: scrapeAssignments() });
      return false;
    }
    return false; // not for us
  });
})();
