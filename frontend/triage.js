import { COHORT } from "/static/cohort_data.js";
import { STATUS, statusFromRisk, statusLabel, statusClass, reasonsToSentence, avatarBackground, avatarInitials } from "/static/status.js";

const STATUS_PRIORITY = { [STATUS.AT_RISK]: 0, [STATUS.CHECK_IN]: 1, [STATUS.STEADY]: 2, [STATUS.THRIVING]: 3 };

function reasonContext(student, reasons) {
  if (!reasons || reasons.length === 0) return {};
  const overrides = student.reason_overrides ?? {};
  return overrides[reasons[0]] ?? {};
}

async function scoreStudent(student) {
  try {
    const res = await fetch("/predictive/dropout-risk", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        engagement: student.engagement,
        reflection_count: student.reflection_count,
      }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    // Apply explicit reason overrides from cohort_data (calling drift, etc.).
    // Each override key adds 1 point to the score (mirrors backend's reason→score weighting)
    // and adds the reason to the reasons array if not already there.
    if (student.reason_overrides) {
      const extras = Object.keys(student.reason_overrides).filter(
        (r) => !(data.reasons ?? []).includes(r),
      );
      data.reasons = [...(data.reasons ?? []), ...extras];
      data.score = (data.score ?? 0) + extras.length;
    }
    return { student, data };
  } catch (err) {
    return { student, data: null, error: String(err) };
  }
}

function buildRow(scored) {
  const { student, data } = scored;
  const status = statusFromRisk({ score: data?.score ?? 0 });
  const row = document.createElement("a");
  row.href = `/students/${student.id}`;
  row.className = "triage-row";
  row.dataset.testid = "triage-row";
  row.dataset.status = status;
  row.dataset.studentId = student.id;

  const avatar = document.createElement("span");
  avatar.className = "avatar";
  avatar.style.background = avatarBackground(student.name);
  avatar.textContent = avatarInitials(student.name);
  avatar.setAttribute("aria-hidden", "true");
  row.appendChild(avatar);

  const content = document.createElement("div");
  content.className = "triage-content";
  const name = document.createElement("p");
  name.className = "triage-name";
  name.textContent = student.name;
  const reason = document.createElement("p");
  reason.className = "triage-reason";
  reason.dataset.testid = "triage-reason";
  reason.textContent = reasonsToSentence(data?.reasons ?? [], reasonContext(student, data?.reasons));
  content.appendChild(name);
  content.appendChild(reason);
  row.appendChild(content);

  const pill = document.createElement("span");
  pill.className = `status-pill ${statusClass(status)} triage-pill`;
  pill.dataset.testid = "triage-status-pill";
  pill.textContent = statusLabel(status);
  row.appendChild(pill);

  const action = document.createElement("span");
  action.className = "triage-action";
  action.textContent = status === STATUS.THRIVING || status === STATUS.STEADY ? "Profile →" : "Schedule →";
  row.appendChild(action);

  return { row, status };
}

async function init() {
  const list = document.querySelector("[data-testid='triage-list']");
  const summary = document.querySelector("[data-testid='triage-summary']");
  if (!list) return;

  const scored = await Promise.all(COHORT.map(scoreStudent));
  const total = scored.length;
  const flagged = scored.filter(
    (s) => statusFromRisk({ score: s.data?.score ?? 0 }) === STATUS.AT_RISK ||
           statusFromRisk({ score: s.data?.score ?? 0 }) === STATUS.CHECK_IN,
  );

  // Sort: at-risk first, then checkin, then steady, then thriving
  const sorted = [...scored].sort((a, b) => {
    const sa = statusFromRisk({ score: a.data?.score ?? 0 });
    const sb = statusFromRisk({ score: b.data?.score ?? 0 });
    return STATUS_PRIORITY[sa] - STATUS_PRIORITY[sb];
  });

  // Show only the flagged + 2 thriving as context (5 rows max for triage focus)
  const display = flagged.length > 0
    ? sorted.slice(0, Math.min(flagged.length + 1, 6))
    : sorted.slice(0, 0);

  list.innerHTML = "";
  list.removeAttribute("aria-busy");

  if (display.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.dataset.testid = "triage-empty-state";
    empty.textContent = "No one needs a check-in this week. The cohort is steady.";
    list.appendChild(empty);
    summary.textContent = `${total} students · all steady`;
    return;
  }

  display.forEach((scoredItem) => {
    const { row } = buildRow(scoredItem);
    list.appendChild(row);
  });

  summary.textContent = `${total} students · ${flagged.length} need attention this week`;
}

init();
