import { COHORT } from "/static/cohort_data.js";
import { avatarBackground, avatarInitials } from "/static/status.js";

const ROSTER_ID = "__roster__";
const GROUPS = ["alpha", "beta", "gamma"];

// In-memory state: groupId → student[].
const state = {
  [ROSTER_ID]: [...COHORT],
  alpha: [],
  beta: [],
  gamma: [],
};

function dropTargetFor(groupId) {
  return document.querySelector(`[data-group-id="${groupId}"][data-testid$="-drop"], [data-testid="roster-drop"][data-group-id="${groupId}"]`)
    ?? document.querySelector(`[data-testid="${groupId}-drop"]`);
}

function buildChip(student) {
  const chip = document.createElement("div");
  chip.className = "student-chip";
  chip.draggable = true;
  chip.dataset.testid = "student-chip";
  chip.dataset.studentId = student.id;
  chip.setAttribute("aria-grabbed", "false");
  chip.tabIndex = 0;

  const av = document.createElement("span");
  av.className = "avatar sm";
  av.style.background = avatarBackground(student.name);
  av.textContent = avatarInitials(student.name);
  av.setAttribute("aria-hidden", "true");
  chip.appendChild(av);

  const name = document.createElement("span");
  name.textContent = student.name;
  chip.appendChild(name);

  chip.addEventListener("dragstart", (e) => {
    chip.classList.add("dragging");
    chip.setAttribute("aria-grabbed", "true");
    e.dataTransfer.setData("text/plain", student.id);
    e.dataTransfer.effectAllowed = "move";
  });
  chip.addEventListener("dragend", () => {
    chip.classList.remove("dragging");
    chip.setAttribute("aria-grabbed", "false");
  });

  return chip;
}

function findStudentLocation(studentId) {
  for (const groupId of [ROSTER_ID, ...GROUPS]) {
    if (state[groupId].some((s) => s.id === studentId)) return groupId;
  }
  return null;
}

function moveStudent(studentId, toGroup) {
  const fromGroup = findStudentLocation(studentId);
  if (!fromGroup || fromGroup === toGroup) return;
  const student = state[fromGroup].find((s) => s.id === studentId);
  state[fromGroup] = state[fromGroup].filter((s) => s.id !== studentId);
  state[toGroup].push(student);
  rerender();
}

function rerender() {
  const targets = {
    [ROSTER_ID]: document.querySelector("[data-testid='roster-drop']"),
    alpha: document.querySelector("[data-testid='alpha-drop']"),
    beta: document.querySelector("[data-testid='beta-drop']"),
    gamma: document.querySelector("[data-testid='gamma-drop']"),
  };
  for (const [groupId, el] of Object.entries(targets)) {
    if (!el) continue;
    el.innerHTML = "";
    state[groupId].forEach((s) => el.appendChild(buildChip(s)));
  }
  // Counts
  document.querySelector("[data-testid='roster-count']").textContent = state[ROSTER_ID].length;
  document.querySelector("[data-testid='alpha-count']").textContent = state.alpha.length;
  document.querySelector("[data-testid='beta-count']").textContent = state.beta.length;
  document.querySelector("[data-testid='gamma-count']").textContent = state.gamma.length;
}

function wireDropTargets() {
  document.querySelectorAll(".groups-drop-target").forEach((target) => {
    target.addEventListener("dragover", (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
      target.classList.add("drag-over");
    });
    target.addEventListener("dragleave", () => target.classList.remove("drag-over"));
    target.addEventListener("drop", (e) => {
      e.preventDefault();
      target.classList.remove("drag-over");
      const studentId = e.dataTransfer.getData("text/plain");
      const groupId = target.dataset.groupId;
      if (studentId && groupId) moveStudent(studentId, groupId);
    });
  });
}

function autoDistribute() {
  // Round-robin every roster student into the 3 groups.
  GROUPS.forEach((g) => { state[g] = []; });
  state[ROSTER_ID].forEach((s, i) => state[GROUPS[i % 3]].push(s));
  state[ROSTER_ID] = [];
  rerender();
  showToast("Distributed across 3 groups.");
}

async function suggest() {
  const payload = GROUPS.map((g) => ({ id: g, members: state[g].map((s) => s.name) }));
  try {
    const res = await fetch("/orchestration/actions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderSuggestions(data.actions ?? []);
  } catch (err) {
    showToast(`Couldn't fetch suggestions: ${err.message}`, true);
  }
}

function renderSuggestions(actions) {
  const block = document.querySelector("[data-testid='groups-suggestions']");
  block.innerHTML = "";
  if (!actions || actions.length === 0) {
    block.innerHTML = `
      <h3>No changes recommended</h3>
      <p>Your groups look balanced. You can confirm the plan as-is.</p>
    `;
    block.hidden = false;
    return;
  }
  const heading = document.createElement("h3");
  heading.textContent = `${actions.length} suggestion${actions.length === 1 ? "" : "s"}`;
  const list = document.createElement("ul");
  actions.forEach((a) => {
    const li = document.createElement("li");
    li.dataset.testid = "groups-suggestion-item";
    if (a.action === "merge_group") {
      li.textContent = `Group ${a.group_id} has ${a.member_count} members — consider merging it with another small group (${a.reason.replaceAll("_", " ")}).`;
    } else {
      li.textContent = `${a.action.replaceAll("_", " ")}${a.group_id ? ` — group ${a.group_id}` : ""}`;
    }
    list.appendChild(li);
  });
  block.appendChild(heading);
  block.appendChild(list);
  block.hidden = false;
}

function confirmPlan() {
  const unassigned = state[ROSTER_ID].length;
  if (unassigned > 0) {
    showToast(`${unassigned} student${unassigned === 1 ? "" : "s"} still in the roster — distribute them first.`, true);
    return;
  }
  const summary = GROUPS.map((g) => `${g}: ${state[g].length}`).join(" · ");
  showToast(`Plan confirmed. ${summary}`);
}

let toastTimer = null;
function showToast(message, isError = false) {
  const toast = document.querySelector("[data-testid='groups-toast']");
  toast.textContent = message;
  toast.style.background = isError ? "var(--accent)" : "var(--ink)";
  toast.hidden = false;
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toast.hidden = true; }, 3000);
}

function init() {
  rerender();
  wireDropTargets();
  document.querySelector("[data-testid='groups-distribute']").addEventListener("click", autoDistribute);
  document.querySelector("[data-testid='groups-suggest']").addEventListener("click", suggest);
  document.querySelector("[data-testid='groups-confirm']").addEventListener("click", confirmPlan);
}

init();
