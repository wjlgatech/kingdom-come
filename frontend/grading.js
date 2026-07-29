// Grading review surface. All state lives on the server (grading_data/);
// this page is a thin client over /api/grading/*. The finalize button is
// THE human gate — nothing is official until the professor clicks it.

const $ = (sel) => document.querySelector(sel);

let drafts = [];
let selectedId = null;

async function api(path, options = {}) {
  const res = await fetch(`/api/grading${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const detail = (await res.json().catch(() => ({}))).detail || res.statusText;
    throw new Error(detail);
  }
  return res.json();
}

function setStatus(msg, isError = false) {
  const el = $('[data-testid="status-line"]');
  el.textContent = msg;
  el.style.color = isError ? "var(--status-risk)" : "var(--ink-muted)";
}

function renderList() {
  const list = $('[data-testid="draft-list"]');
  list.setAttribute("aria-busy", "false");
  list.innerHTML = "";
  const finalized = drafts.filter((d) => d.status === "final").length;
  $('[data-testid="grading-progress"]').textContent =
    drafts.length ? `${finalized} / ${drafts.length} 已定稿` : "";
  $('[data-testid="empty-state"]').hidden = drafts.length > 0;

  for (const d of drafts) {
    const row = document.createElement("button");
    row.type = "button";
    row.className = "draft-row" + (d.id === selectedId ? " selected" : "");
    row.dataset.testid = "draft-row";
    const chips = [];
    if (d.needs_attention && d.status !== "final") chips.push('<span class="status-chip attention">注意</span>');
    chips.push(`<span class="status-chip ${d.status}">${d.status === "final" ? "已定稿" : "草稿"}</span>`);
    row.innerHTML = `
      <span class="row-student"></span>
      <span class="row-meta"><span class="row-grade">${d.grade ?? "—"}</span>${chips.join("")}</span>`;
    row.querySelector(".row-student").textContent = d.student;
    row.addEventListener("click", () => selectDraft(d.id));
    list.appendChild(row);
  }
}

function renderDetail(d) {
  $('[data-testid="draft-detail"]').hidden = false;
  $('[data-testid="detail-student"]').textContent = d.student;
  const statusChip = $('[data-testid="detail-status"]');
  statusChip.className = `status-chip ${d.status}`;
  statusChip.textContent = d.status === "final" ? "已定稿" : "草稿";

  const flagsBox = $('[data-testid="detail-flags"]');
  flagsBox.hidden = !(d.flag_notes || []).length;
  flagsBox.textContent = (d.flag_notes || []).length ? "⚠ " + d.flag_notes.join("；") : "";

  $('[data-testid="report-text"]').textContent = d.report_text || "（未找到原始报告文件）";
  $('[data-testid="grade-input"]').value = d.grade ?? "";
  $('[data-testid="comment-editor"]').value = d.comment || "";
  $('[data-testid="rationale-text"]').textContent = d.rationale || "—";

  const isFinal = d.status === "final";
  $('[data-testid="grade-input"]').disabled = isFinal;
  $('[data-testid="comment-editor"]').disabled = isFinal;
  $('[data-testid="save-btn"]').disabled = isFinal;
  $('[data-testid="regen-btn"]').disabled = isFinal;
  $('[data-testid="regen-input"]').disabled = isFinal;
  $('[data-testid="finalize-btn"]').hidden = isFinal;
  $('[data-testid="reopen-btn"]').hidden = !isFinal;
}

async function refreshList() {
  drafts = (await api("/drafts")).drafts;
  renderList();
}

async function selectDraft(id) {
  selectedId = id;
  renderList();
  setStatus("");
  renderDetail(await api(`/drafts/${encodeURIComponent(id)}`));
}

async function saveEdits() {
  const grade = Number($('[data-testid="grade-input"]').value);
  const comment = $('[data-testid="comment-editor"]').value;
  await api(`/drafts/${encodeURIComponent(selectedId)}`, {
    method: "PUT",
    body: JSON.stringify({ grade, comment }),
  });
  await refreshList();
  setStatus("已保存。");
}

async function finalize() {
  await saveEdits(); // never finalize stale text — persist the editor first
  await api(`/drafts/${encodeURIComponent(selectedId)}/finalize`, { method: "POST" });
  await refreshList();
  await selectDraft(selectedId); // re-fetch: transition responses carry no report_text
  setStatus("已定稿 ✓");
}

async function reopen() {
  await api(`/drafts/${encodeURIComponent(selectedId)}/reopen`, { method: "POST" });
  await refreshList();
  await selectDraft(selectedId);
  setStatus("已重新打开。");
}

async function regenerate() {
  const guidance = $('[data-testid="regen-input"]').value.trim();
  if (!guidance) return setStatus("请先写下修改指示。", true);
  setStatus("AI 正在按指示重写……");
  $('[data-testid="regen-btn"]').disabled = true;
  try {
    const d = await api(`/drafts/${encodeURIComponent(selectedId)}/regenerate`, {
      method: "POST",
      body: JSON.stringify({ guidance }),
    });
    d.report_text = $('[data-testid="report-text"]').textContent;
    renderDetail(d);
    await refreshList();
    setStatus("重写完成——请审阅。");
  } finally {
    $('[data-testid="regen-btn"]').disabled = false;
  }
}

function guard(fn) {
  return () => fn().catch((e) => setStatus(e.message, true));
}

$('[data-testid="save-btn"]').addEventListener("click", guard(saveEdits));
$('[data-testid="finalize-btn"]').addEventListener("click", guard(finalize));
$('[data-testid="reopen-btn"]').addEventListener("click", guard(reopen));
$('[data-testid="regen-btn"]').addEventListener("click", guard(regenerate));

refreshList().then(() => {
  if (drafts.length) selectDraft(drafts[0].id);
}).catch((e) => setStatus(e.message, true));
