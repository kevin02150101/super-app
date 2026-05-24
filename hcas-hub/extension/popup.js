const DEFAULT_HUB = "http://127.0.0.1:8000";
const $ = (id) => document.getElementById(id);

const TEAMS_RE = /(teams\.microsoft\.com|teams\.cloud\.microsoft|teams\.live\.com)/;
const ASSIGNMENTS_FRAME_RE = /^https:\/\/assignments\.edu\.cloud\.microsoft\//i;
const POWERSCHOOL_RE = /(\.powerschool\.com|\.powerschool\.cloud)/i;

(async function init() {
  // Restore saved Hub URL
  const { hubUrl } = await chrome.storage.sync.get({ hubUrl: DEFAULT_HUB });
  $("hub").value = hubUrl;

  // Save button (explicit)
  $("save").addEventListener("click", saveHubUrl);
  $("hub").addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); saveHubUrl(); }
  });
  $("hub").addEventListener("input", () => {
    const btn = $("save");
    btn.classList.remove("saved");
    btn.textContent = "Save";
  });

  $("open").addEventListener("click", async () => {
    const { hubUrl } = await chrome.storage.sync.get({ hubUrl: DEFAULT_HUB });
    chrome.tabs.create({ url: hubUrl });
  });

  $("openAssignments").addEventListener("click", async () => {
    const { hubUrl } = await chrome.storage.sync.get({ hubUrl: DEFAULT_HUB });
    const base = (hubUrl || DEFAULT_HUB).replace(/\/+$/, "");
    chrome.tabs.create({ url: base + "/assignments" });
  });

  $("refresh").addEventListener("click", () => refreshPreview());

  $("sync").addEventListener("click", doSync);

  await refreshPreview();
})();

async function saveHubUrl() {
  const url = ($("hub").value || "").trim() || DEFAULT_HUB;
  await chrome.storage.sync.set({ hubUrl: url });
  $("hub").value = url;
  const btn = $("save");
  btn.classList.add("saved");
  btn.textContent = "Saved";
  setStatus(`Hub URL saved: ${url}`, "ok");
  setTimeout(() => {
    btn.classList.remove("saved");
    btn.textContent = "Save";
  }, 1800);
}

async function getActiveSupportedTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) return null;
  const url = tab.url || "";
  if (TEAMS_RE.test(url)) return { tab, kind: "teams" };
  if (POWERSCHOOL_RE.test(url)) return { tab, kind: "powerschool" };
  return null;
}

async function getActiveTeamsTab() {
  const hit = await getActiveSupportedTab();
  return hit && hit.kind === "teams" ? hit.tab : null;
}

// Find the iframe inside the Teams tab that hosts the Assignments app.
// Returns its frameId, or 0 (top frame) as a fallback.
async function findAssignmentsFrameId(tabId) {
  try {
    const frames = await chrome.webNavigation.getAllFrames({ tabId });
    if (!frames) return 0;
    const hit = frames.find((f) => ASSIGNMENTS_FRAME_RE.test(f.url || ""));
    return hit ? hit.frameId : 0;
  } catch {
    return 0;
  }
}

function sendToFrame(tabId, frameId, message) {
  return new Promise((resolve) => {
    chrome.tabs.sendMessage(tabId, message, { frameId }, (resp) => {
      if (chrome.runtime.lastError) resolve({ ok: false, error: chrome.runtime.lastError.message });
      else resolve(resp || { ok: false, error: "no response" });
    });
  });
}

// If the content script is missing (e.g. extension was reloaded after the
// tab was opened), inject it on demand so the user doesn't have to refresh.
async function ensureContentScript(tabId, kind) {
  const file = kind === "teams" ? "content.js" : "powerschool.js";
  try {
    await chrome.scripting.executeScript({
      target: { tabId, allFrames: kind === "teams" },
      files: [file],
    });
    return true;
  } catch (e) {
    return false;
  }
}

async function sendToFrameWithReinject(tab, kind, frameId, message) {
  let resp = await sendToFrame(tab.id, frameId, message);
  const err = (resp && resp.error) || "";
  if (!resp.ok && /Receiving end does not exist|Could not establish connection/i.test(err)) {
    const injected = await ensureContentScript(tab.id, kind);
    if (injected) {
      await new Promise((r) => setTimeout(r, 250));
      resp = await sendToFrame(tab.id, frameId, message);
    }
  }
  return resp;
}

async function refreshPreview() {
  setPageStatus("Checking…", "neutral");
  const hit = await getActiveSupportedTab();
  if (!hit) {
    setPageStatus("Not on Teams/PS", "warn");
    $("foundCount").textContent = "—";
    renderPreview([]);
    setStatus("Open a Microsoft Teams tab (Assignments) or a PowerSchool page with an assignments table.");
    $("sync").disabled = true;
    return;
  }
  setPageStatus(hit.kind === "teams" ? "On Teams" : "On PowerSchool", "ok");
  $("sync").disabled = false;

  let frameId = 0;
  if (hit.kind === "teams") {
    frameId = await findAssignmentsFrameId(hit.tab.id);
  }
  const resp = await sendToFrameWithReinject(hit.tab, hit.kind, frameId, { type: "PEEK_ROWS" });

  if (!resp.ok && resp.error) {
    setPageStatus("Reload page", "err");
    setStatus("Couldn't talk to the page. Reload the tab and reopen this popup. (" + resp.error + ")", "err");
    return;
  }
  $("foundCount").textContent = resp.rows ? resp.rows.length : 0;
  renderPreview(resp.rows || []);
  if (!resp.rows || resp.rows.length === 0) {
    setStatus(hit.kind === "teams"
      ? "On Teams but no assignment rows visible. Click 'Assignments' in Teams' left rail and scroll."
      : "On PowerSchool but no assignment table on this page. Open a Class Score Detail or Assignments page.");
  } else {
    setStatus(`Ready to sync ${resp.rows.length} assignment(s).`, "ok");
  }
}

function renderPreview(rows) {
  const list = $("previewList");
  list.innerHTML = "";
  if (!rows.length) {
    list.innerHTML = '<li class="empty" style="border:0;color:var(--mute);">No assignments visible yet.</li>';
    return;
  }
  for (const r of rows.slice(0, 20)) {
    const li = document.createElement("li");
    const t = document.createElement("span"); t.className = "a-title"; t.textContent = r.title || "(untitled)";
    const m = document.createElement("span"); m.className = "a-meta";
    const parts = [];
    if (r.subject) parts.push(r.subject);
    if (r.due_at)  parts.push("due " + formatDue(r.due_at));
    m.textContent = parts.join("  ·  ") || "no metadata";
    li.appendChild(t); li.appendChild(m);
    list.appendChild(li);
  }
  if (rows.length > 20) {
    const li = document.createElement("li");
    li.className = "empty";
    li.style.color = "var(--mute)";
    li.textContent = `+${rows.length - 20} more…`;
    list.appendChild(li);
  }
}

function formatDue(iso) {
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
  } catch { return iso; }
}

async function doSync() {
  const hit = await getActiveSupportedTab();
  if (!hit) {
    setStatus("Open a Teams or PowerSchool tab first.", "err");
    return;
  }
  $("sync").disabled = true;
  setStatus("Syncing…");
  const frameId = hit.kind === "teams" ? await findAssignmentsFrameId(hit.tab.id) : 0;
  const resp = await sendToFrameWithReinject(hit.tab, hit.kind, frameId, { type: "TRIGGER_SYNC" });
  $("sync").disabled = false;
  if (resp && resp.ok) {
    const detail = resp.added !== undefined
      ? `+${resp.added} new, ${resp.updated} updated`
      : "sent";
    setStatus(`Synced. ${detail}`, "ok");
    setTimeout(refreshPreview, 600);
  } else {
    setStatus("Sync failed: " + (resp ? resp.error : "no response"), "err");
  }
}

function setStatus(msg, tone) {
  const el = $("status");
  el.textContent = msg;
  el.className = "status" + (tone ? " " + tone : "");
}

function setPageStatus(text, tone) {
  $("pageStatusText").textContent = text;
  const pill = $("pageStatus");
  pill.classList.remove("ok", "warn", "err", "neutral");
  pill.classList.add(tone || "neutral");
}
