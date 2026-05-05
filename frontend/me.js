import { findStudent } from "/static/cohort_data.js";
import { STATUS, statusFromRisk, statusLabel, statusClass, reasonsToSentence } from "/static/status.js";

function safeLs() { try { return window.localStorage; } catch { return null; } }

function todayString() {
  const d = new Date();
  const day = d.toLocaleDateString("en-US", { weekday: "long" });
  // "Tuesday · 5 May 2026"
  const date = d.toLocaleDateString("en-US", { day: "numeric", month: "long", year: "numeric" });
  return `${day} · ${date}`;
}

function setText(testid, value) {
  const el = document.querySelector(`[data-testid="${testid}"]`);
  if (el) el.textContent = value;
}

function renderStatusLine(student, riskJson) {
  const status = statusFromRisk({ score: riskJson.score });
  const ctx = student.reason_overrides?.[riskJson.reasons?.[0]] ?? {};
  const reasonText = (() => {
    if (riskJson.reasons && riskJson.reasons.length > 0) return reasonsToSentence(riskJson.reasons, ctx);
    if (status === STATUS.THRIVING) return "Reflecting consistently this week.";
    return "Holding pattern this week.";
  })();
  const line = document.querySelector("[data-testid='me-status-line']");
  if (!line) return;
  line.innerHTML = "";
  const pill = document.createElement("span");
  pill.className = `status-pill ${statusClass(status)}`;
  pill.textContent = statusLabel(status);
  pill.dataset.testid = "me-status-pill";
  line.appendChild(pill);
  line.appendChild(document.createTextNode(" "));
  const sentence = document.createElement("span");
  sentence.dataset.testid = "me-status-reason";
  sentence.textContent = reasonText;
  line.appendChild(sentence);
}

function renderPathLine(student, recsJson) {
  const line = document.querySelector("[data-testid='me-path-line']");
  if (!line) return;
  line.innerHTML = "";
  const recs = recsJson.recommendations ?? [];
  if (recs.length === 0) {
    line.classList.add("empty-state");
    line.textContent = "Your formation path is still being shaped. Check back after your first 1:1.";
    return;
  }
  const next = recs[0].replaceAll("_", " ");
  const strong = document.createElement("strong");
  strong.style.fontWeight = "500";
  strong.textContent = next.charAt(0).toUpperCase() + next.slice(1);
  line.appendChild(strong);
  line.appendChild(document.createTextNode(" — three short readings before next Tuesday's small group."));
}

function showCardError(testid) {
  const line = document.querySelector(`[data-testid="${testid}"]`);
  if (!line) return;
  line.innerHTML = "";
  line.classList.add("kc-error");
  line.textContent = "Couldn't load. Try again in a minute.";
}

async function init() {
  const ls = safeLs();
  const studentId = ls?.getItem("kc-student-id") ?? "stu-marcus-r";
  const student = findStudent(studentId);
  if (!student) {
    setText("me-name", "Friend");
    return;
  }

  setText("me-name", student.name.split(" ")[0]);
  setText("me-date", todayString());

  // Fetch dropout risk + curriculum recs in parallel.
  const [riskRes, recsRes] = await Promise.allSettled([
    fetch("/predictive/dropout-risk", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ engagement: student.engagement, reflection_count: student.reflection_count }),
    }).then((r) => r.json()),
    fetch("/curriculum/recommendations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ calling: student.calling, completed_content: [] }),
    }).then((r) => r.json()),
  ]);

  if (riskRes.status === "fulfilled") renderStatusLine(student, riskRes.value);
  else showCardError("me-status-line");

  if (recsRes.status === "fulfilled") renderPathLine(student, recsRes.value);
  else showCardError("me-path-line");
}

init();
