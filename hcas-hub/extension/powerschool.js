// HCAS Hub — PowerSchool Schedule Sync
// Scrapes the student's class schedule (My Schedule / Class Schedule page)
// and posts it to /api/import_schedule on the local Hub.

(() => {
  if (window.__hcasHubPSLoaded) return;
  window.__hcasHubPSLoaded = true;

  const STATE = { lastFound: 0 };
  const log = (...a) => console.log("[HCAS Hub · PS Schedule]", ...a);

  function headerIndex(headers, ...patterns) {
    for (let i = 0; i < headers.length; i++) {
      for (const p of patterns) if (p.test(headers[i])) return i;
    }
    return -1;
  }
  function cellText(cells, idx) {
    if (idx < 0 || !cells[idx]) return "";
    return (cells[idx].innerText || cells[idx].textContent || "")
      .replace(/\s+/g, " ").trim();
  }

  function findScheduleTables() {
    const out = [];
    const allTables = Array.from(document.querySelectorAll("table"));
    const debugRows = [];
    for (const tbl of allTables) {
      // Build header row from thead OR first row with th's OR any row with th's
      let headerCells = tbl.querySelectorAll("thead th");
      if (!headerCells.length) headerCells = tbl.querySelectorAll("tr th");
      if (!headerCells.length) {
        // Fall back to first row td's
        const firstRow = tbl.querySelector("tr");
        headerCells = firstRow ? firstRow.querySelectorAll("td") : [];
      }
      const headers = Array.from(headerCells).map(
        (c) => (c.textContent || "").trim().toLowerCase()
      );
      debugRows.push({ headers, rows: tbl.querySelectorAll("tr").length, cls: tbl.className });
      log("table headers:", tbl.className, headers);
      if (!headers.length) continue;
      // Reject assignment / grade tables.
      if (headers.some((h) => /due|score|points|category|^grade$|^%$|^percent/.test(h))) continue;

      const colPeriod  = headerIndex(headers, /^(period|exp(ression)?|block|hr|pd)\b/, /period|block|expression/);
      const colCourse  = headerIndex(headers, /^course\b/, /class\s*name/, /^name$/, /course|class|subject/);
      const colTeacher = headerIndex(headers, /teacher|instructor|staff/);
      const colRoom    = headerIndex(headers, /room|location/);
      const colDays    = headerIndex(headers, /days|meeting|day\(s\)/);
      const colTime    = headerIndex(headers, /time|meets/);
      if (colCourse < 0) continue;
      if (colPeriod < 0 && colTime < 0 && colTeacher < 0 && colRoom < 0) continue;

      log("schedule-like table found", { headers, colPeriod, colCourse, colTeacher, colRoom, colDays, colTime });
      out.push({ table: tbl, cols: {
        period: colPeriod, course: colCourse, teacher: colTeacher,
        room: colRoom, days: colDays, time: colTime,
      }});
    }
    if (!out.length) {
      log("no schedule tables matched. Total tables on page:", allTables.length);
      log("all table headers seen:", debugRows);
    }
    return out;
  }

  function splitTime(text) {
    if (!text) return { start: "", end: "" };
    const m = text.match(
      /(\d{1,2}:\d{2}\s*(?:AM|PM)?)\s*[-–—]+\s*(\d{1,2}:\d{2}\s*(?:AM|PM)?)/i
    );
    if (m) return { start: m[1].toUpperCase(), end: m[2].toUpperCase() };
    return { start: text, end: "" };
  }

  function scrapeMatrixSchedule() {
    // PowerSchool myschedule.html — weekly matrix. Header row is days of
    // the week, body cells contain "Pd N(X)\nCourse\nTeacher - Rm 123".
    const out = [];
    const table = document.querySelector("table.gridSched");
    if (!table) return out;
    const DAY_RE = /(monday|tuesday|wednesday|thursday|friday|saturday|sunday)/i;
    const DAY_SHORT = { monday:"M", tuesday:"T", wednesday:"W", thursday:"R", friday:"F", saturday:"S", sunday:"U" };
    // Build column -> day map from the header row.
    const headerCells = table.querySelectorAll("tr th, tr:first-child td, tr:first-child th");
    const colDay = {};
    Array.from(headerCells).forEach((c, i) => {
      const m = DAY_RE.exec((c.textContent || "").toLowerCase());
      if (m) colDay[i] = DAY_SHORT[m[1].toLowerCase()];
    });
    log("matrix day columns:", colDay);
    // Total column count from the header row (so rowspan tracking lines up).
    const headerRow = table.querySelector("tr");
    const totalCols = headerRow
      ? Array.from(headerRow.children).filter((c) => c.tagName === "TD" || c.tagName === "TH").length
      : 7;

    // Map from external_id -> aggregated row.
    const map = new Map();
    // rowspanLeft[col] = number of subsequent rows where this column is
    // already occupied by a previous TD with rowspan > 1.
    const rowspanLeft = new Array(totalCols).fill(0);
    const allRows = Array.from(table.querySelectorAll("tr"));
    for (const tr of allRows) {
      const tds = Array.from(tr.children).filter((c) => c.tagName === "TD" || c.tagName === "TH");
      // Skip ONLY the day-of-week header row (contains "Monday 05/.." etc.).
      // Empty filler rows still need to flow through so rowspanLeft decrements.
      const isDayHeader = tds.some((c) => DAY_RE.test((c.textContent || "").toLowerCase()));
      if (isDayHeader) continue;
      let tdIdx = 0;
      for (let col = 0; col < totalCols; col++) {
        if (rowspanLeft[col] > 0) {
          rowspanLeft[col]--;
          continue;
        }
        const td = tds[tdIdx++];
        if (!td) break;
        const rs = parseInt(td.getAttribute("rowspan") || "1", 10);
        if (rs > 1) rowspanLeft[col] = rs - 1;
        const cs = parseInt(td.getAttribute("colspan") || "1", 10);
        const day = colDay[col];
        // Advance col by colspan-1 extra steps (we'll let the for-loop ++ handle the +1).
        if (cs > 1) col += cs - 1;
        if (!day) continue;
        const txt = (td.innerText || td.textContent || "").replace(/\u00A0/g, " ").trim();
        if (!txt || txt.length < 3) continue;
        // Skip pure date cells and day-name/date stub cells.
        if (/^\d{1,2}\/\d{1,2}\/\d{2,4}$/.test(txt)) continue;
        const firstLine = txt.split(/\n/)[0].trim().toLowerCase();
        if (DAY_RE.test(firstLine) && firstLine.length < 12) continue;
        // Pull out time range first.
        const TIME_RANGE = /(\d{1,2}:\d{2}\s*(?:AM|PM))\s*[-–—]+\s*(\d{1,2}:\d{2}\s*(?:AM|PM))/i;
        const mTime = txt.match(TIME_RANGE);
        const start_time = mTime ? mTime[1].toUpperCase().replace(/\s+/g, " ") : "";
        const end_time   = mTime ? mTime[2].toUpperCase().replace(/\s+/g, " ") : "";
        const noTime = mTime ? (txt.slice(0, mTime.index) + txt.slice(mTime.index + mTime[0].length)) : txt;
        const lines = noTime.split(/\n+/).map((s) => s.replace(/\s+/g, " ").trim()).filter(Boolean);
        if (!lines.length) continue;
        const course = (lines[0] || "").slice(0, 120);
        if (!course) continue;
        const teacher = (lines[1] || "").slice(0, 80);
        const room = "";
        const period = "";
        const key = `powerschool::${start_time || "?"}-${end_time || "?"}::${course}`;
        const existing = map.get(key);
        if (existing) {
          if (!existing.days.includes(day)) existing.days += day;
          if (!existing.teacher && teacher) existing.teacher = teacher;
        } else {
          map.set(key, {
            course, teacher, room, period, days: day,
            start_time, end_time,
            source: "powerschool", external_id: key,
          });
        }
      }
    }
    for (const v of map.values()) out.push(v);
    log("matrix scraped:", out);
    out.forEach((r, i) => log(`  [${i}]`, r.days, r.start_time + "-" + r.end_time, r.course, "/", r.teacher));
    return out;
  }

  function scrapeSchedule() {
    // Try matrix view (myschedule.html) first.
    const matrix = scrapeMatrixSchedule();
    if (matrix.length) return matrix;

    const rows = [];
    for (const { table, cols } of findScheduleTables()) {
      for (const tr of table.querySelectorAll("tbody tr, tr")) {
        const cells = tr.querySelectorAll("td");
        if (!cells.length) continue;
        const course = cellText(cells, cols.course).slice(0, 120);
        if (!course || /^course$/i.test(course)) continue;
        const period  = cellText(cells, cols.period).slice(0, 20);
        const teacher = cellText(cells, cols.teacher).slice(0, 80);
        const room    = cellText(cells, cols.room).slice(0, 40);
        const days    = cellText(cells, cols.days).slice(0, 20);
        const { start, end } = splitTime(cellText(cells, cols.time));
        const external_id = `powerschool::${period || "?"}::${course}`;
        rows.push({ course, teacher, room, period, days,
                    start_time: start, end_time: end,
                    source: "powerschool", external_id });
      }
    }
    const map = new Map();
    for (const r of rows) map.set(r.external_id, r);
    return Array.from(map.values());
  }

  // ─── Badge ───────────────────────────────────────────────────────────
  const BADGE_POS_KEY = "hcasBadgePosPSSchedule";

  function applyPosition(badge, left, top) {
    const w = badge.offsetWidth || 200, h = badge.offsetHeight || 40;
    left = Math.max(4, Math.min(left, window.innerWidth - w - 4));
    top  = Math.max(4, Math.min(top,  window.innerHeight - h - 4));
    badge.style.left = left + "px"; badge.style.top = top + "px";
    badge.style.right = "auto"; badge.style.bottom = "auto";
  }
  function ensureBadge() {
    let badge = document.getElementById("hcas-hub-ps-sync-badge");
    if (!badge) {
      badge = document.createElement("div");
      badge.id = "hcas-hub-ps-sync-badge";
      Object.assign(badge.style, {
        position: "fixed", right: "16px", bottom: "16px", zIndex: 999999,
        background: "#0F1A2F", color: "#F5F7FA",
        font: '700 12px/1.2 -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, sans-serif',
        padding: "10px 14px 10px 28px",
        border: "1px solid rgba(255,128,32,0.45)",
        borderRadius: "8px", cursor: "grab",
        boxShadow: "0 6px 20px rgba(15,26,47,0.45)",
        letterSpacing: "0.10em", textTransform: "uppercase", userSelect: "none",
      });
      badge.title = "Click to sync your PowerSchool schedule to HCAS Hub";
      const grip = document.createElement("span");
      Object.assign(grip.style, {
        position: "absolute", left: "8px", top: "50%", transform: "translateY(-50%)",
        width: "8px", height: "14px",
        backgroundImage: "radial-gradient(circle, rgba(245,247,250,0.65) 1px, transparent 1.2px)",
        backgroundSize: "4px 4px",
      });
      badge.appendChild(grip);
      const label = document.createElement("span");
      label.id = "hcas-hub-ps-sync-badge-label";
      badge.appendChild(label);
      try {
        chrome.storage.local.get(BADGE_POS_KEY, (data) => {
          const pos = data && data[BADGE_POS_KEY];
          if (pos && typeof pos.left === "number" && typeof pos.top === "number") {
            applyPosition(badge, pos.left, pos.top);
          }
        });
      } catch {}
      attachDrag(badge);
      badge.addEventListener("click", () => {
        if (badge.dataset.dragged === "1") { badge.dataset.dragged = "0"; return; }
        sync();
      });
      document.body.appendChild(badge);
    }
    const label = badge.querySelector("#hcas-hub-ps-sync-badge-label");
    if (label) label.textContent = `Sync schedule${STATE.lastFound ? ` · ${STATE.lastFound}` : ""}`;
    badge.style.display = STATE.lastFound ? "" : "none";
  }
  function attachDrag(badge) {
    let sx=0, sy=0, ox=0, oy=0, moved=0, dragging=false;
    function down(ev) {
      ev.preventDefault(); dragging=true; moved=0;
      badge.dataset.dragged="0"; badge.style.cursor="grabbing";
      const r = badge.getBoundingClientRect(); ox=r.left; oy=r.top;
      const p = ev.touches ? ev.touches[0] : ev;
      sx=p.clientX; sy=p.clientY;
      document.addEventListener("mousemove", move);
      document.addEventListener("mouseup", up);
    }
    function move(ev) {
      if (!dragging) return; ev.preventDefault();
      const p = ev.touches ? ev.touches[0] : ev;
      const dx=p.clientX-sx, dy=p.clientY-sy;
      moved = Math.max(moved, Math.abs(dx)+Math.abs(dy));
      applyPosition(badge, ox+dx, oy+dy);
    }
    function up() {
      if (!dragging) return; dragging=false;
      badge.style.cursor="grab";
      document.removeEventListener("mousemove", move);
      document.removeEventListener("mouseup", up);
      if (moved>4) {
        badge.dataset.dragged="1";
        try {
          const r = badge.getBoundingClientRect();
          chrome.storage.local.set({ [BADGE_POS_KEY]: { left:r.left, top:r.top } });
        } catch {}
      }
    }
    badge.addEventListener("mousedown", down);
  }

  function isContextValid() {
    try { return !!(chrome && chrome.runtime && chrome.runtime.id); } catch { return false; }
  }

  function sync() {
    return new Promise((resolve) => {
      if (!isContextValid()) {
        resolve({ ok:false, error:"Extension reloaded. Refresh this PowerSchool tab." });
        return;
      }
      const badge = document.getElementById("hcas-hub-ps-sync-badge");
      const rows = scrapeSchedule();
      STATE.lastFound = rows.length;
      log("syncing schedule", rows);
      if (badge) badge.textContent = `Syncing ${rows.length}…`;
      try {
        chrome.runtime.sendMessage(
          { type: "IMPORT_SCHEDULE", rows, replace: true },
          (resp) => {
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
                badge.style.borderColor = "rgba(255,128,32,0.45)";
                badge.style.color = "#F5F7FA";
                ensureBadge();
              }, 4000);
            }
            resolve(resp || { ok:false, error:"no response" });
          }
        );
      } catch (err) {
        resolve({ ok:false, error: err.message });
      }
    });
  }

  function tick() {
    if (!isContextValid()) { clearInterval(tickHandle); return; }
    STATE.lastFound = scrapeSchedule().length;
    ensureBadge();
  }
  const tickHandle = setInterval(tick, 3000);
  tick();

  chrome.runtime.onMessage.addListener((msg, _s, sendResponse) => {
    if (msg && msg.type === "TRIGGER_SYNC") {
      sync().then((r) => sendResponse(r));
      return true; // async
    }
    if (msg && msg.type === "PEEK_ROWS") {
      sendResponse({ ok: true, rows: scrapeSchedule() });
      return false;
    }
    return false; // not for us — let other listeners handle it
  });
})();
