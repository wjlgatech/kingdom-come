import { findStudent, getProfile } from "/static/cohort_data.js";
import { STATUS, statusFromRisk, statusLabel, statusClass, avatarBackground, avatarInitials } from "/static/status.js";

const studentId = window.STUDENT_ID;
const student = findStudent(studentId);

function renderNotFound() {
  document.querySelector(".profile-main").innerHTML = `
    <div class="profile-not-found" data-testid="profile-not-found">
      Student not found in this cohort.
      <p style="margin-top: var(--space-16);"><a href="/cohort/triage" class="btn btn-secondary">← Back to triage</a></p>
    </div>
  `;
}

if (!student) {
  renderNotFound();
} else {
  initProfile();
}

async function initProfile() {
  const profile = getProfile(studentId);

  // Header
  const avatar = document.querySelector("[data-testid='profile-avatar']");
  avatar.style.background = avatarBackground(student.name);
  avatar.textContent = avatarInitials(student.name);
  document.querySelector("[data-testid='profile-name']").textContent = student.name;
  document.querySelector("[data-testid='profile-meta']").textContent = `Cohort: St. Aloysius S26 · Calling: ${(student.calling ?? []).join(", ")}`;
  document.querySelector("[data-testid='profile-breadcrumb-name']").textContent = student.name;
  document.title = `${student.name} — Kingdom Come`;

  // Status pill in header
  const riskRes = await fetch("/predictive/dropout-risk", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ engagement: student.engagement, reflection_count: student.reflection_count }),
  }).then((r) => r.json()).catch(() => ({ score: 0 }));
  if (student.reason_overrides) {
    const extras = Object.keys(student.reason_overrides).filter(
      (r) => !(riskRes.reasons ?? []).includes(r),
    );
    riskRes.score = (riskRes.score ?? 0) + extras.length;
  }
  const status = statusFromRisk({ score: riskRes.score });
  const pillSlot = document.querySelector("[data-testid='profile-status-pill']");
  const pill = document.createElement("span");
  pill.className = `status-pill ${statusClass(status)}`;
  pill.textContent = statusLabel(status);
  pillSlot.appendChild(pill);

  // Tabs
  setupTabs();

  // Panels
  renderReflections(profile.reflections);
  renderOutcomes(profile.outcomes);
  renderRiskHistory(profile.risk_history);

  // Outcome modal
  document.querySelector("[data-testid='profile-log-outcome']").addEventListener("click", openOutcomeModal);
}

function setupTabs() {
  const tabs = Array.from(document.querySelectorAll(".profile-tab"));
  const panels = {
    reflections: document.querySelector("[data-testid='panel-reflections']"),
    outcomes: document.querySelector("[data-testid='panel-outcomes']"),
    history: document.querySelector("[data-testid='panel-history']"),
  };
  function activate(name) {
    tabs.forEach((t) => {
      const isActive = t.dataset.tab === name;
      t.setAttribute("aria-selected", isActive ? "true" : "false");
      t.tabIndex = isActive ? 0 : -1;
    });
    Object.entries(panels).forEach(([key, panel]) => {
      panel.hidden = key !== name;
    });
  }
  tabs.forEach((tab, idx) => {
    tab.addEventListener("click", () => activate(tab.dataset.tab));
    tab.addEventListener("keydown", (e) => {
      let next = null;
      if (e.key === "ArrowRight") next = tabs[(idx + 1) % tabs.length];
      else if (e.key === "ArrowLeft") next = tabs[(idx - 1 + tabs.length) % tabs.length];
      else if (e.key === "Home") next = tabs[0];
      else if (e.key === "End") next = tabs[tabs.length - 1];
      if (next) {
        e.preventDefault();
        activate(next.dataset.tab);
        next.focus();
      }
    });
  });
}

function renderReflections(items) {
  const panel = document.querySelector("[data-testid='panel-reflections']");
  panel.innerHTML = "";
  if (!items || items.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.dataset.testid = "panel-empty";
    empty.textContent = `${student.name.split(" ")[0]} hasn't logged a reflection yet.`;
    panel.appendChild(empty);
    return;
  }
  items.forEach((r) => {
    const entry = document.createElement("article");
    entry.className = "profile-entry";
    entry.dataset.testid = "reflection-entry";
    entry.innerHTML = `
      <div class="profile-entry-meta"><span>${r.date}</span></div>
      <div class="profile-entry-body">${r.excerpt}</div>
    `;
    panel.appendChild(entry);
  });
}

function renderOutcomes(items) {
  const panel = document.querySelector("[data-testid='panel-outcomes']");
  panel.innerHTML = "";
  if (!items || items.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.dataset.testid = "panel-empty";
    empty.textContent = `Log ${student.name.split(" ")[0]}'s first ministry outcome with the button above.`;
    panel.appendChild(empty);
    return;
  }
  items.forEach((o) => panel.appendChild(outcomeEntry(o)));
}

function outcomeEntry(o) {
  const entry = document.createElement("article");
  entry.className = "profile-entry";
  entry.dataset.testid = "outcome-entry";
  const tag =
    o.effectiveness === "strong" ? "Strong" :
    o.effectiveness === "developing" ? "Developing" : "Needs support";
  entry.innerHTML = `
    <div class="profile-entry-meta"><span>${o.date}</span><span>${tag} · impact ${o.impact_score.toFixed(2)}</span></div>
    <div class="profile-entry-body">${o.description}</div>
  `;
  return entry;
}

function renderRiskHistory(items) {
  const panel = document.querySelector("[data-testid='panel-history']");
  panel.innerHTML = "";
  if (!items || items.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "Building your risk picture — 3 weeks of data needed.";
    panel.appendChild(empty);
    return;
  }
  const wrap = document.createElement("div");
  wrap.className = "profile-history";
  items.forEach((h) => {
    const week = document.createElement("div");
    week.className = "profile-history-week";
    const pill = document.createElement("span");
    pill.className = `status-pill ${statusClass(h.status)}`;
    pill.textContent = statusLabel(h.status);
    week.appendChild(pill);
    const label = document.createElement("span");
    label.textContent = h.week;
    week.appendChild(label);
    wrap.appendChild(week);
  });
  panel.appendChild(wrap);
}

// ---- Outcome modal ----

let modalEl = null;
let lastFocus = null;

function openOutcomeModal() {
  lastFocus = document.activeElement;
  modalEl = document.createElement("div");
  modalEl.className = "kc-modal-backdrop";
  modalEl.dataset.testid = "outcome-modal";
  modalEl.innerHTML = `
    <div class="kc-modal" role="dialog" aria-modal="true" aria-labelledby="outcome-modal-title">
      <button type="button" class="kc-modal-close" data-testid="outcome-modal-close" aria-label="Close">×</button>
      <h2 id="outcome-modal-title" style="font-family: var(--serif-display); font-weight: 400; margin: 0 0 var(--space-24);">
        Log outcome for ${student.name}
      </h2>
      <form data-testid="outcome-form-modal">
        <div class="kc-field">
          <label for="impact-score">Impact score (0–1)</label>
          <input type="range" id="impact-score" name="impact_score" min="0" max="1" step="0.05" value="0.65" />
          <div class="range-value" data-testid="impact-value">0.65</div>
        </div>
        <div class="kc-field">
          <label for="outcome-description">Description</label>
          <textarea id="outcome-description" name="description" rows="4" required placeholder="What did they do?"></textarea>
        </div>
        <div data-testid="outcome-error-slot"></div>
        <div style="display: flex; gap: var(--space-12); justify-content: flex-end; margin-top: var(--space-24);">
          <button type="button" class="btn btn-ghost" data-testid="outcome-modal-cancel">Cancel</button>
          <button type="submit" class="btn btn-primary" data-testid="outcome-modal-save">Save</button>
        </div>
      </form>
    </div>
  `;
  document.body.appendChild(modalEl);

  // Focus trap setup
  const dialog = modalEl.querySelector(".kc-modal");
  const focusable = dialog.querySelectorAll("button, input, textarea, [tabindex]:not([tabindex='-1'])");
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  first.focus();

  const range = modalEl.querySelector("input[type='range']");
  const rangeValue = modalEl.querySelector("[data-testid='impact-value']");
  range.addEventListener("input", () => { rangeValue.textContent = Number(range.value).toFixed(2); });

  modalEl.addEventListener("click", (e) => { if (e.target === modalEl) closeOutcomeModal(); });
  modalEl.querySelector("[data-testid='outcome-modal-close']").addEventListener("click", closeOutcomeModal);
  modalEl.querySelector("[data-testid='outcome-modal-cancel']").addEventListener("click", closeOutcomeModal);

  modalEl.addEventListener("keydown", (e) => {
    if (e.key === "Escape") { closeOutcomeModal(); return; }
    if (e.key === "Tab") {
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });

  modalEl.querySelector("[data-testid='outcome-form-modal']").addEventListener("submit", submitOutcome);
}

function closeOutcomeModal() {
  if (!modalEl) return;
  modalEl.remove();
  modalEl = null;
  lastFocus?.focus();
}

async function submitOutcome(e) {
  e.preventDefault();
  const form = e.currentTarget;
  const impact = Number(form.impact_score.value);
  const description = form.description.value.trim();
  const errorSlot = modalEl.querySelector("[data-testid='outcome-error-slot']");
  errorSlot.innerHTML = "";

  try {
    const res = await fetch("/outcomes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ student_id: studentId, impact_score: impact, description }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || `HTTP ${res.status}`);
    }
    const saved = await res.json();
    saved.date = new Date().toISOString().slice(0, 10);
    // Insert into Outcomes panel at top
    const panel = document.querySelector("[data-testid='panel-outcomes']");
    const empty = panel.querySelector(".empty-state");
    if (empty) empty.remove();
    panel.insertBefore(outcomeEntry(saved), panel.firstChild);
    // Switch to outcomes tab
    document.querySelector("[data-testid='tab-outcomes']").click();
    closeOutcomeModal();
  } catch (err) {
    const toast = document.createElement("div");
    toast.className = "kc-error";
    toast.dataset.testid = "outcome-error";
    toast.textContent = `Save failed: ${err.message}. Try again.`;
    errorSlot.appendChild(toast);
  }
}
