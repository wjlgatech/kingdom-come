import { findStudent, getProfile } from "/static/cohort_data.js";
import { statusLabel } from "/static/status.js";

const WEEK_HEADLINES = {
  "Week 7": "A heaviness you carried.",
  "Week 6": "Showing up under weight.",
  "Week 5": "Mid-semester strain.",
  "Week 4": "A rhythm starting to crack.",
  "Week 3": "Settling into the work.",
  "Week 2": "Finding your hands.",
  "Week 1": "Beginnings.",
};

const CURRICULUM_FOR_WEEK = {
  "Week 7": "Mission theology — three short readings.",
  "Week 6": "A rest week — no new content.",
  "Week 5": "Pastoral counseling primer.",
  "Week 4": "General theology — synoptic gospels.",
  "Week 3": "Field practice — supervised cohort visit.",
  "Week 2": "First small-group facilitation.",
  "Week 1": "Discernment readings.",
};

function safeLs() { try { return window.localStorage; } catch { return null; } }

function pickReflectionForWeek(reflections, weekLabel) {
  // Map oldest reflection to Week 1, working backwards. Defensive against
  // mismatched lengths (more weeks than reflections is the common case).
  if (!reflections || reflections.length === 0) return null;
  const sorted = [...reflections].sort((a, b) => a.date.localeCompare(b.date));
  const weekNum = Number(weekLabel.replace("Week ", ""));
  // Most recent reflection corresponds to the most recent week with data.
  const reverseIdx = 7 - weekNum; // Week 7 → idx 0 from the end
  const idx = sorted.length - 1 - reverseIdx;
  if (idx < 0 || idx >= sorted.length) return null;
  return sorted[idx];
}

function pickOutcomeForWeek(outcomes, weekLabel) {
  if (!outcomes || outcomes.length === 0) return null;
  // Naive: round-robin into the last weeks based on date order.
  const weekNum = Number(weekLabel.replace("Week ", ""));
  const sorted = [...outcomes].sort((a, b) => a.date.localeCompare(b.date));
  const idx = sorted.length - (8 - weekNum);
  return idx >= 0 && idx < sorted.length ? sorted[idx] : null;
}

function buildWeekCard(week, idxFromMostRecent, profile, isFirst) {
  const card = document.createElement("article");
  card.className = `timeline-week ${week.status}`;
  if (isFirst) card.classList.add("first");
  card.dataset.testid = "timeline-week";
  card.dataset.week = week.week;

  const label = document.createElement("div");
  label.className = "timeline-week-label";
  const weekText = document.createElement("span");
  weekText.textContent = week.week;
  const pill = document.createElement("span");
  pill.className = `status-pill status-${week.status}`;
  pill.textContent = statusLabel(week.status);
  label.appendChild(weekText);
  label.appendChild(pill);
  card.appendChild(label);

  const headline = document.createElement("h2");
  headline.className = "timeline-week-headline";
  headline.textContent = WEEK_HEADLINES[week.week] ?? week.week;
  card.appendChild(headline);

  // Reflection
  const reflection = pickReflectionForWeek(profile.reflections, week.week);
  const refSection = document.createElement("div");
  refSection.className = "timeline-section reflection";
  const refLabel = document.createElement("div");
  refLabel.className = "timeline-section-label";
  refLabel.textContent = "What you wrote";
  const refBody = document.createElement("p");
  refBody.className = "timeline-section-body";
  if (reflection) {
    refBody.textContent = reflection.excerpt;
    refBody.dataset.testid = "timeline-reflection";
  } else {
    refBody.classList.add("muted");
    refBody.textContent = "No reflection logged this week.";
  }
  refSection.appendChild(refLabel);
  refSection.appendChild(refBody);
  card.appendChild(refSection);

  // Outcome
  const outcome = pickOutcomeForWeek(profile.outcomes, week.week);
  if (outcome) {
    const oSection = document.createElement("div");
    oSection.className = "timeline-section outcome";
    const oLabel = document.createElement("div");
    oLabel.className = "timeline-section-label";
    oLabel.textContent = "Ministry outcome";
    const oBody = document.createElement("p");
    oBody.className = "timeline-section-body";
    oBody.dataset.testid = "timeline-outcome";
    oBody.textContent = outcome.description;
    oSection.appendChild(oLabel);
    oSection.appendChild(oBody);
    card.appendChild(oSection);
  }

  // Curriculum (only for the most recent week, as "next step")
  if (isFirst) {
    const cSection = document.createElement("div");
    cSection.className = "timeline-section curriculum";
    const cLabel = document.createElement("div");
    cLabel.className = "timeline-section-label";
    cLabel.textContent = "Next in your path";
    const cBody = document.createElement("p");
    cBody.className = "timeline-section-body muted";
    cBody.textContent = CURRICULUM_FOR_WEEK[week.week] ?? "";
    cSection.appendChild(cLabel);
    cSection.appendChild(cBody);
    card.appendChild(cSection);
  }

  return card;
}

function init() {
  const ls = safeLs();
  const studentId = ls?.getItem("kc-student-id") ?? "stu-marcus-r";
  const student = findStudent(studentId);
  const list = document.querySelector("[data-testid='timeline-list']");
  list.removeAttribute("aria-busy");
  list.innerHTML = "";

  if (!student) {
    list.innerHTML = `<div class="empty-state" data-testid="timeline-empty">No formation arc available — student not found.</div>`;
    return;
  }

  const profile = getProfile(studentId);
  const history = profile.risk_history ?? [];

  if (history.length < 1) {
    list.innerHTML = `<div class="empty-state" data-testid="timeline-empty">Your arc starts after your first week. Come back Sunday.</div>`;
    return;
  }

  // Most recent week first.
  const ordered = [...history].reverse();
  ordered.forEach((week, idx) => {
    list.appendChild(buildWeekCard(week, idx, profile, idx === 0));
  });
}

init();
