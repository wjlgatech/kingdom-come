import { COHORT, findStudent, DEMO_DIRECTOR, DEMO_SEMINARIAN_ID } from "/static/cohort_data.js";

function safeLs() { try { return window.localStorage; } catch { return null; } }
const ls = safeLs();
const me = ls?.getItem("kc-student-id") ?? DEMO_SEMINARIAN_ID;

// ---- status vocabulary (pastoral labels; never raw enum values) ----

const PRAYER_STATUS = {
  open: { label: "Open", cls: "status-steady" },
  watching: { label: "Watching", cls: "status-checkin" },
  answered_yes: { label: "Answered", cls: "status-thriving" },
  partial: { label: "Answered in part", cls: "status-checkin" },
  no: { label: "Not as asked", cls: "status-risk" },
  superseded: { label: "Superseded", cls: "status-steady" },
};

const PROPHECY_STATUS = {
  spoken: { label: "Spoken", cls: "status-steady" },
  weighing: { label: "Being weighed", cls: "status-checkin" },
  confirmed: { label: "Confirmed", cls: "status-thriving" },
  refined: { label: "Refine & re-speak", cls: "status-checkin" },
  rejected: { label: "Not confirmed", cls: "status-risk" },
};

const FULFILLMENT_LABEL = {
  pending: "Fulfillment open",
  fulfilled: "Fulfilled",
  partial: "Fulfilled in part",
  unfulfilled: "Unfulfilled",
};

const VISIBILITY_LABEL = {
  private: "Private",
  small_group: "Small group",
  cohort: "Whole cohort",
};

function nameOf(id) {
  if (id === DEMO_DIRECTOR.id) return DEMO_DIRECTOR.name;
  return findStudent(id)?.name ?? id;
}

function pill(map, status) {
  const def = map[status] ?? { label: status, cls: "status-steady" };
  const el = document.createElement("span");
  el.className = `status-pill ${def.cls}`;
  el.textContent = def.label;
  return el;
}

function dateOf(iso) { return (iso ?? "").slice(0, 10); }

async function getJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function detailToMessage(detail, status) {
  // FastAPI 422 detail is a list of objects; flatten to readable text.
  if (Array.isArray(detail)) return detail.map((d) => d?.msg ?? JSON.stringify(d)).join("; ");
  if (typeof detail === "string") return detail;
  return `HTTP ${status}`;
}

async function sendJSON(url, body, method = "POST") {
  const res = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(detailToMessage(data.detail, res.status));
  }
  return res.json();
}

// Wrap a fire-and-forget action button so a failed request re-enables the
// button and shows the user something, instead of failing silently.
async function guardAction(button, fn) {
  const prev = button.disabled;
  button.disabled = true;
  try {
    await fn();
  } catch (err) {
    button.disabled = prev;
    const toast = document.createElement("div");
    toast.className = "kc-error";
    toast.textContent = `Couldn't do that: ${err.message}. Try again.`;
    button.insertAdjacentElement("afterend", toast);
  }
}

// ---- tabs (same ARIA pattern as the student-profile tab bar) ----

const tabs = [
  { tab: "[data-testid='prayer-tab-prayers']", panel: "[data-testid='prayer-panel-prayers']" },
  { tab: "[data-testid='prayer-tab-words']", panel: "[data-testid='prayer-panel-words']" },
  { tab: "[data-testid='prayer-tab-weigh']", panel: "[data-testid='prayer-panel-weigh']" },
].map(({ tab, panel }) => ({
  tab: document.querySelector(tab),
  panel: document.querySelector(panel),
}));

function activateTab(idx) {
  tabs.forEach(({ tab, panel }, i) => {
    tab.setAttribute("aria-selected", i === idx ? "true" : "false");
    tab.tabIndex = i === idx ? 0 : -1;
    panel.hidden = i !== idx;
  });
}

tabs.forEach(({ tab }, idx) => {
  tab.addEventListener("click", () => activateTab(idx));
  tab.addEventListener("keydown", (e) => {
    let next = null;
    if (e.key === "ArrowRight") next = (idx + 1) % tabs.length;
    else if (e.key === "ArrowLeft") next = (idx - 1 + tabs.length) % tabs.length;
    else if (e.key === "Home") next = 0;
    else if (e.key === "End") next = tabs.length - 1;
    if (next !== null) {
      e.preventDefault();
      activateTab(next);
      tabs[next].tab.focus();
    }
  });
});

// ---- shared modal helper (focus trap + ESC, same idiom as profile.js) ----

let modalEl = null;
let lastFocus = null;

function openModal(title, formHtml, onSubmit) {
  lastFocus = document.activeElement;
  modalEl = document.createElement("div");
  modalEl.className = "kc-modal-backdrop";
  modalEl.dataset.testid = "prayer-modal";
  modalEl.innerHTML = `
    <div class="kc-modal" role="dialog" aria-modal="true" aria-labelledby="prayer-modal-title">
      <button type="button" class="kc-modal-close" data-testid="prayer-modal-close" aria-label="Close">×</button>
      <h2 id="prayer-modal-title" style="font-family: var(--serif-display); font-weight: 400; margin: 0 0 var(--space-24);"></h2>
      <form data-testid="prayer-modal-form">
        ${formHtml}
        <div data-testid="prayer-modal-error-slot"></div>
        <div style="display: flex; gap: var(--space-12); justify-content: flex-end; margin-top: var(--space-24);">
          <button type="button" class="btn btn-ghost" data-testid="prayer-modal-cancel">Cancel</button>
          <button type="submit" class="btn btn-primary" data-testid="prayer-modal-save">Save</button>
        </div>
      </form>
    </div>
  `;
  modalEl.querySelector("#prayer-modal-title").textContent = title;
  document.body.appendChild(modalEl);

  const dialog = modalEl.querySelector(".kc-modal");
  const focusable = dialog.querySelectorAll("button, input, textarea, select, [tabindex]:not([tabindex='-1'])");
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  first.focus();

  modalEl.addEventListener("click", (e) => { if (e.target === modalEl) closeModal(); });
  modalEl.querySelector("[data-testid='prayer-modal-close']").addEventListener("click", closeModal);
  modalEl.querySelector("[data-testid='prayer-modal-cancel']").addEventListener("click", closeModal);
  modalEl.addEventListener("keydown", (e) => {
    if (e.key === "Escape") { closeModal(); return; }
    if (e.key === "Tab") {
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });

  const form = modalEl.querySelector("[data-testid='prayer-modal-form']");
  const saveBtn = modalEl.querySelector("[data-testid='prayer-modal-save']");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (saveBtn.disabled) return;  // guard against double-submit
    const errorSlot = modalEl.querySelector("[data-testid='prayer-modal-error-slot']");
    errorSlot.innerHTML = "";
    saveBtn.disabled = true;
    try {
      await onSubmit(form);
      closeModal();
    } catch (err) {
      saveBtn.disabled = false;
      const toast = document.createElement("div");
      toast.className = "kc-error";
      toast.dataset.testid = "prayer-modal-error";
      toast.textContent = `Save failed: ${err.message}. Try again.`;
      errorSlot.appendChild(toast);
    }
  });
  return modalEl;
}

function closeModal() {
  if (!modalEl) return;
  modalEl.remove();
  modalEl = null;
  lastFocus?.focus();
}

// Returns [{id, name}] for a roster <select>. Callers append options via
// document.createElement so a (future) user-entered name can't inject HTML.
function rosterPeople(excludeIds = []) {
  return [...COHORT, DEMO_DIRECTOR].filter((p) => !excludeIds.includes(p.id));
}

function fillSelect(select, people) {
  people.forEach((p) => {
    const opt = document.createElement("option");
    opt.value = p.id;
    opt.textContent = p.name;
    select.appendChild(opt);
  });
}

// ---- track record line ----

async function renderTrackRecord() {
  const slot = document.querySelector("[data-testid='prayer-track-record']");
  try {
    const data = await getJSON(`/api/prayer/track-record/${encodeURIComponent(me)}`);
    const pr = data.prayer;
    const ph = data.prophecy;
    const parts = [
      `${pr.total} petition${pr.total === 1 ? "" : "s"}`,
      `${pr.answered_favorable} answered`,
      `${ph.total_spoken} word${ph.total_spoken === 1 ? "" : "s"} spoken`,
      `${ph.by_status?.confirmed ?? 0} confirmed`,
    ];
    slot.textContent = parts.join(" · ");
  } catch {
    slot.textContent = "Track record unavailable right now.";
  }
}

// ---- my prayers panel ----

function prayerCard(p) {
  const card = document.createElement("article");
  card.className = "ledger-card";
  card.dataset.testid = "prayer-card";
  card.dataset.prayerId = p.id;

  const top = document.createElement("div");
  top.className = "ledger-card-top";
  const text = document.createElement("p");
  text.className = "ledger-text";
  text.textContent = p.petition;
  top.appendChild(text);
  top.appendChild(pill(PRAYER_STATUS, p.status));
  card.appendChild(top);

  const meta = document.createElement("div");
  meta.className = "ledger-meta";
  const metaBits = [dateOf(p.created_at), VISIBILITY_LABEL[p.visibility] ?? p.visibility];
  if ((p.intercessions ?? []).length > 0) {
    metaBits.push(`${p.intercessions.length} praying with you`);
  }
  metaBits.forEach((m) => {
    const s = document.createElement("span");
    s.textContent = m;
    meta.appendChild(s);
  });
  if (p.scripture) {
    const s = document.createElement("span");
    s.className = "scripture";
    s.textContent = p.scripture;
    meta.appendChild(s);
  }
  card.appendChild(meta);

  if (p.answer?.testimony) {
    const quote = document.createElement("blockquote");
    quote.className = "ledger-quote";
    quote.dataset.testid = "prayer-testimony";
    quote.textContent = p.answer.testimony;
    card.appendChild(quote);
  }

  if (!["answered_yes", "partial", "no", "superseded"].includes(p.status)) {
    const actions = document.createElement("div");
    actions.className = "ledger-actions";
    if (p.status === "open") {
      const watch = document.createElement("button");
      watch.type = "button";
      watch.className = "btn btn-ghost inline";
      watch.dataset.testid = "prayer-watch";
      watch.textContent = "Start watching →";
      watch.addEventListener("click", () => guardAction(watch, async () => {
        await sendJSON(`/api/prayer/requests/${p.id}/watch`, {});
        await loadPrayers();
        renderTrackRecord();
      }));
      actions.appendChild(watch);
    }
    const answer = document.createElement("button");
    answer.type = "button";
    answer.className = "btn btn-ghost inline";
    answer.dataset.testid = "prayer-mark-answered";
    answer.textContent = "Mark answered →";
    answer.addEventListener("click", () => openAnswerModal(p));
    actions.appendChild(answer);
    card.appendChild(actions);
  }
  return card;
}

function peerPrayerCard(p) {
  const card = document.createElement("article");
  card.className = "ledger-card";
  card.dataset.testid = "peer-prayer-card";

  const top = document.createElement("div");
  top.className = "ledger-card-top";
  const text = document.createElement("p");
  text.className = "ledger-text";
  text.textContent = p.petition;
  top.appendChild(text);
  top.appendChild(pill(PRAYER_STATUS, p.status));
  card.appendChild(top);

  const meta = document.createElement("div");
  meta.className = "ledger-meta";
  const who = document.createElement("span");
  who.textContent = `${nameOf(p.student_id)} · ${dateOf(p.created_at)}`;
  meta.appendChild(who);
  card.appendChild(meta);

  const mine = (p.intercessions ?? []).some((i) => i.peer_id === me);
  const actions = document.createElement("div");
  actions.className = "ledger-actions";
  if (mine) {
    const done = document.createElement("span");
    done.className = "ledger-meta";
    done.textContent = "You are praying with them.";
    actions.appendChild(done);
  } else {
    const pray = document.createElement("button");
    pray.type = "button";
    pray.className = "btn btn-secondary";
    pray.dataset.testid = "prayer-intercede";
    pray.textContent = "Pray with them";
    pray.addEventListener("click", () => guardAction(pray, async () => {
      await sendJSON(`/api/prayer/requests/${p.id}/intercessions`, { peer_id: me, message: "Praying with you." });
      await loadPrayers();
    }));
    actions.appendChild(pray);
  }
  card.appendChild(actions);
  return card;
}

async function loadPrayers() {
  const list = document.querySelector("[data-testid='prayer-list']");
  try {
    const visible = (await getJSON(`/api/prayer/requests?visible_to=${encodeURIComponent(me)}`)).prayers;
    const detailed = await Promise.all(
      visible.map((p) => getJSON(`/api/prayer/requests/${p.id}`).catch(() => p)),
    );
    const mine = detailed.filter((p) => p.student_id === me);
    const peers = detailed.filter((p) => p.student_id !== me);

    list.innerHTML = "";
    list.setAttribute("aria-busy", "false");
    if (mine.length === 0) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.dataset.testid = "prayer-empty";
      empty.textContent = "Bring your first petition. Nothing here is graded — it is witnessed.";
      list.appendChild(empty);
    } else {
      mine.forEach((p) => list.appendChild(prayerCard(p)));
    }

    if (peers.length > 0) {
      const h = document.createElement("h2");
      h.className = "me-card-label";
      h.style.marginTop = "var(--space-32)";
      h.textContent = "Carried together";
      list.appendChild(h);
      peers.forEach((p) => list.appendChild(peerPrayerCard(p)));
    }
  } catch {
    list.innerHTML = "";
    list.setAttribute("aria-busy", "false");
    const err = document.createElement("div");
    err.className = "kc-error";
    err.textContent = "Couldn't load the prayer ledger. Try again in a minute.";
    list.appendChild(err);
  }
}

function openPetitionModal() {
  const modal = openModal(
    "Bring a petition",
    `
    <div class="kc-field">
      <label for="petition-text">Petition *</label>
      <textarea id="petition-text" name="petition" rows="4" required placeholder="What are you carrying?"></textarea>
    </div>
    <div class="kc-field">
      <label for="petition-scripture">Scripture (optional)</label>
      <input type="text" id="petition-scripture" name="scripture" placeholder="e.g. James 1:5" />
    </div>
    <div class="kc-field">
      <label for="petition-visibility">Who sees this</label>
      <select id="petition-visibility" name="visibility">
        <option value="private" selected>Only me (private)</option>
        <option value="small_group">Chosen peers (small group)</option>
        <option value="cohort">Whole cohort</option>
      </select>
    </div>
    <div class="kc-field" data-testid="petition-recipients-field" hidden>
      <label for="petition-recipients">Share with (choose peers)</label>
      <select id="petition-recipients" name="recipients" multiple size="5"></select>
    </div>
    `,
    async (form) => {
      const visibility = form.visibility.value;
      const recipients = Array.from(form.querySelector("#petition-recipients").selectedOptions).map((o) => o.value);
      await sendJSON("/api/prayer/requests", {
        student_id: me,
        petition: form.petition.value.trim(),
        scripture: form.scripture.value.trim() || null,
        visibility,
        recipient_ids: visibility === "small_group" ? recipients : [],
      });
      await loadPrayers();
      renderTrackRecord();
    },
  );
  fillSelect(modal.querySelector("#petition-recipients"), rosterPeople([me]));
  const visSelect = modal.querySelector("#petition-visibility");
  const recipientsField = modal.querySelector("[data-testid='petition-recipients-field']");
  visSelect.addEventListener("change", () => {
    recipientsField.hidden = visSelect.value !== "small_group";
  });
}

function openAnswerModal(p) {
  openModal(
    "How was it answered?",
    `
    <div class="kc-field">
      <label for="answer-status">Answer</label>
      <select id="answer-status" name="status">
        <option value="answered_yes" selected>Answered</option>
        <option value="partial">Answered in part</option>
        <option value="no">Not as asked</option>
        <option value="superseded">Superseded — the asking changed</option>
      </select>
    </div>
    <div class="kc-field">
      <label for="answer-testimony">Testimony *</label>
      <textarea id="answer-testimony" name="testimony" rows="4" required placeholder="What happened?"></textarea>
    </div>
    `,
    async (form) => {
      await sendJSON(`/api/prayer/requests/${p.id}/answer`, {
        status: form.status.value,
        testimony: form.testimony.value.trim(),
      });
      await loadPrayers();
      renderTrackRecord();
    },
  );
}

// ---- words panel ----

function wordCard(p) {
  const card = document.createElement("article");
  card.className = "ledger-card";
  card.dataset.testid = "word-card";

  const top = document.createElement("div");
  top.className = "ledger-card-top";
  const text = document.createElement("p");
  text.className = "ledger-text";
  text.textContent = p.word;
  top.appendChild(text);
  top.appendChild(pill(PROPHECY_STATUS, p.status));
  card.appendChild(top);

  const meta = document.createElement("div");
  meta.className = "ledger-meta";
  const who = document.createElement("span");
  who.textContent = `${nameOf(p.speaker_id)} → ${nameOf(p.addressed_to)} · ${dateOf(p.created_at)}`;
  meta.appendChild(who);
  const weighed = document.createElement("span");
  weighed.textContent = `${(p.weighings ?? []).length} of ${(p.weigher_ids ?? []).length} weighed`;
  meta.appendChild(weighed);
  if (p.fulfillment) {
    const f = document.createElement("span");
    f.textContent = FULFILLMENT_LABEL[p.fulfillment.status] ?? p.fulfillment.status;
    meta.appendChild(f);
  }
  card.appendChild(meta);

  const refineNote = (p.weighings ?? []).find((w) => w.judgment === "refine" && w.notes);
  if (p.status === "refined" && refineNote) {
    const quote = document.createElement("blockquote");
    quote.className = "ledger-quote";
    quote.textContent = refineNote.notes;
    card.appendChild(quote);
  }
  if (p.fulfillment?.testimony) {
    const quote = document.createElement("blockquote");
    quote.className = "ledger-quote";
    quote.dataset.testid = "word-fulfillment-testimony";
    quote.textContent = p.fulfillment.testimony;
    card.appendChild(quote);
  }

  const canRecord =
    p.status === "confirmed" &&
    (!p.fulfillment || p.fulfillment.status === "pending") &&
    (p.speaker_id === me || p.addressed_to === me);
  if (canRecord) {
    const actions = document.createElement("div");
    actions.className = "ledger-actions";
    const record = document.createElement("button");
    record.type = "button";
    record.className = "btn btn-ghost inline";
    record.dataset.testid = "word-record-fulfillment";
    record.textContent = "Record fulfillment →";
    record.addEventListener("click", () => openFulfillmentModal(p));
    actions.appendChild(record);
    card.appendChild(actions);
  }
  return card;
}

async function loadWords() {
  const list = document.querySelector("[data-testid='word-list']");
  const weighList = document.querySelector("[data-testid='weigh-list']");
  const weighCount = document.querySelector("[data-testid='weigh-count']");
  try {
    const all = (await getJSON(`/api/prophecies?visible_to=${encodeURIComponent(me)}`)).prophecies;
    const mine = all.filter((p) => p.speaker_id === me || p.addressed_to === me);
    const toWeigh = all.filter(
      (p) =>
        (p.weigher_ids ?? []).includes(me) &&
        !(p.weighings ?? []).some((w) => w.weigher_id === me) &&
        ["spoken", "weighing"].includes(p.status),
    );

    list.innerHTML = "";
    list.setAttribute("aria-busy", "false");
    if (mine.length === 0) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.dataset.testid = "word-empty";
      empty.textContent = "No words yet. When one is spoken over you — or by you — it is weighed here.";
      list.appendChild(empty);
    } else {
      mine.forEach((p) => list.appendChild(wordCard(p)));
    }

    weighList.innerHTML = "";
    weighList.setAttribute("aria-busy", "false");
    if (toWeigh.length === 0) {
      weighCount.hidden = true;
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.dataset.testid = "weigh-empty";
      empty.textContent = "No words awaiting your discernment.";
      weighList.appendChild(empty);
    } else {
      weighCount.hidden = false;
      weighCount.textContent = String(toWeigh.length);
      toWeigh.forEach((p) => weighList.appendChild(weighCard(p)));
    }
  } catch {
    [list, weighList].forEach((el) => {
      el.innerHTML = "";
      el.setAttribute("aria-busy", "false");
      const err = document.createElement("div");
      err.className = "kc-error";
      err.textContent = "Couldn't load the prophecy ledger. Try again in a minute.";
      el.appendChild(err);
    });
  }
}

function openSpeakModal() {
  const modal = openModal(
    "Speak a word",
    `
    <div class="kc-field">
      <label for="word-addressed">Addressed to</label>
      <select id="word-addressed" name="addressed_to"></select>
    </div>
    <div class="kc-field">
      <label for="word-text">The word *</label>
      <textarea id="word-text" name="word" rows="4" required placeholder="Speak it as you received it."></textarea>
    </div>
    <div class="kc-field">
      <label for="weigher-1">Weighers — two peers and a leader (1 Cor 14:29)</label>
      <select id="weigher-1" name="weigher1"></select>
    </div>
    <div class="kc-field">
      <label for="weigher-2" class="visually-hidden">Second weigher</label>
      <select id="weigher-2" name="weigher2"></select>
    </div>
    <div class="kc-field">
      <label for="weigher-3" class="visually-hidden">Third weigher</label>
      <select id="weigher-3" name="weigher3"></select>
    </div>
    `,
    async (form) => {
      await sendJSON("/api/prophecies", {
        speaker_id: me,
        addressed_to: form.addressed_to.value,
        word: form.word.value.trim(),
        weigher_ids: [form.weigher1.value, form.weigher2.value, form.weigher3.value],
      });
      await loadWords();
      renderTrackRecord();
    },
  );
  const people = rosterPeople([me]);
  ["#word-addressed", "#weigher-1", "#weigher-2", "#weigher-3"].forEach((sel) =>
    fillSelect(modal.querySelector(sel), people),
  );
}

function openFulfillmentModal(p) {
  openModal(
    "Record fulfillment",
    `
    <div class="kc-field">
      <label for="fulfillment-status">What came of it</label>
      <select id="fulfillment-status" name="status">
        <option value="fulfilled" selected>Fulfilled</option>
        <option value="partial">Fulfilled in part</option>
        <option value="unfulfilled">Unfulfilled</option>
      </select>
    </div>
    <div class="kc-field">
      <label for="fulfillment-testimony">Testimony *</label>
      <textarea id="fulfillment-testimony" name="testimony" rows="4" required placeholder="What happened?"></textarea>
    </div>
    `,
    async (form) => {
      await sendJSON(`/api/prophecies/${p.id}/fulfillment`, {
        status: form.status.value,
        testimony: form.testimony.value.trim(),
      });
      await loadWords();
      renderTrackRecord();
    },
  );
}

// ---- weighing panel ----

function weighCard(p) {
  const card = document.createElement("article");
  card.className = "ledger-card";
  card.dataset.testid = "weigh-card";

  const text = document.createElement("p");
  text.className = "ledger-text";
  text.textContent = p.word;
  card.appendChild(text);

  const meta = document.createElement("div");
  meta.className = "ledger-meta";
  const who = document.createElement("span");
  who.textContent = `${nameOf(p.speaker_id)} → ${nameOf(p.addressed_to)} · ${dateOf(p.created_at)}`;
  meta.appendChild(who);
  card.appendChild(meta);

  const notesWrap = document.createElement("div");
  notesWrap.className = "kc-field weigh-notes";
  notesWrap.style.marginTop = "var(--space-16)";
  const notesLabel = document.createElement("label");
  notesLabel.textContent = "Notes (optional)";
  const notes = document.createElement("textarea");
  notes.rows = 2;
  notes.placeholder = "Why you weigh it this way.";
  notesLabel.appendChild(notes);
  notesWrap.appendChild(notesLabel);
  card.appendChild(notesWrap);

  const actions = document.createElement("div");
  actions.className = "ledger-actions";
  [
    ["confirm", "Confirm", "btn btn-primary"],
    ["refine", "Refine", "btn btn-secondary"],
    ["reject", "Do not confirm", "btn btn-ghost"],
  ].forEach(([judgment, label, cls]) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = cls;
    b.dataset.testid = `weigh-${judgment}`;
    b.textContent = label;
    b.addEventListener("click", async () => {
      actions.querySelectorAll("button").forEach((x) => { x.disabled = true; });
      try {
        await sendJSON(`/api/prophecies/${p.id}/weighings`, {
          weigher_id: me,
          judgment,
          notes: notes.value.trim(),
        });
        await loadWords();
      } catch (err) {
        actions.querySelectorAll("button").forEach((x) => { x.disabled = false; });
        const toast = document.createElement("div");
        toast.className = "kc-error";
        toast.textContent = `Couldn't record the judgment: ${err.message}.`;
        card.appendChild(toast);
      }
    });
    actions.appendChild(b);
  });
  card.appendChild(actions);
  return card;
}

// ---- boot ----

document.querySelector("[data-testid='prayer-new-petition']").addEventListener("click", openPetitionModal);
document.querySelector("[data-testid='prayer-speak-word']").addEventListener("click", openSpeakModal);

renderTrackRecord();
loadPrayers();
loadWords();
