// The Formation Year (10X plan C2): a longitudinal, editorial spread of the
// student's own record — reflections, prayer track record, outcomes, and the
// weekly risk arc. Nothing here is new data; it's the year, assembled.
import { getProfile, findStudent } from "/static/cohort_data.js";
import { statusLabel } from "/static/status.js";

function safeLs() { try { return window.localStorage; } catch { return null; } }
const me = safeLs()?.getItem("kc-student-id") ?? "stu-marcus-r";

function setStat(testid, value) {
  const el = document.querySelector(`[data-testid="${testid}"]`);
  if (el) el.textContent = String(value);
}

function emptyState(text, testid) {
  const div = document.createElement("div");
  div.className = "empty-state";
  if (testid) div.dataset.testid = testid;
  div.textContent = text;
  return div;
}

async function init() {
  const student = findStudent(me);
  const sub = document.querySelector("[data-testid='year-sub']");
  if (student && sub) {
    sub.textContent = `What you reflected, carried, spoke, and did this year, ${student.name.split(" ")[0]} — assembled from your own record.`;
  }

  const [profile, trackRes, prayersRes] = await Promise.all([
    getProfile(me),
    fetch(`/api/prayer/track-record/${encodeURIComponent(me)}`).then((r) => r.json()).catch(() => null),
    fetch(`/api/prayer/requests?student_id=${encodeURIComponent(me)}&visible_to=${encodeURIComponent(me)}`)
      .then((r) => r.json()).catch(() => ({ prayers: [] })),
  ]);

  // Numbers row.
  setStat("year-stat-reflections", profile.reflections.length);
  setStat("year-stat-outcomes", profile.outcomes.length);
  setStat("year-stat-prayers", trackRes?.prayer?.total ?? 0);
  setStat("year-stat-answered", trackRes?.prayer?.answered_favorable ?? 0);

  // Lines you wrote — reflection excerpts as quoted speech.
  const lines = document.querySelector("[data-testid='year-lines']");
  lines.innerHTML = "";
  lines.setAttribute("aria-busy", "false");
  if (profile.reflections.length === 0) {
    lines.appendChild(emptyState("No reflections yet. The year is still being written.", "year-lines-empty"));
  } else {
    profile.reflections.forEach((r) => {
      const q = document.createElement("blockquote");
      q.className = "year-quote";
      q.dataset.testid = "year-line";
      q.textContent = r.excerpt;
      const cite = document.createElement("cite");
      cite.textContent = r.date;
      q.appendChild(cite);
      lines.appendChild(q);
    });
  }

  // Carried and answered — resolved petitions with their testimonies.
  const carried = document.querySelector("[data-testid='year-carried']");
  carried.innerHTML = "";
  carried.setAttribute("aria-busy", "false");
  const answered = (prayersRes.prayers ?? []).filter((p) => p.answer);
  if (answered.length === 0) {
    carried.appendChild(emptyState("Nothing resolved yet — the ledger keeps watch.", "year-carried-empty"));
  } else {
    // Detail fetches for testimonies + intercession counts.
    const detailed = await Promise.all(
      answered.map((p) => fetch(`/api/prayer/requests/${p.id}`).then((r) => r.json()).catch(() => p)),
    );
    detailed.forEach((p) => {
      const item = document.createElement("div");
      item.className = "year-carried-item";
      item.dataset.testid = "year-carried-item";
      const petition = document.createElement("p");
      petition.className = "year-carried-petition";
      petition.textContent = p.petition;
      item.appendChild(petition);
      if (p.answer?.testimony) {
        const t = document.createElement("blockquote");
        t.className = "year-quote";
        t.textContent = p.answer.testimony;
        item.appendChild(t);
      }
      carried.appendChild(item);
    });
  }

  // The arc of your weeks — status words joined into one line.
  const arc = document.querySelector("[data-testid='year-arc']");
  if (profile.risk_history.length === 0) {
    arc.textContent = "The arc begins with your first week.";
  } else {
    arc.textContent = profile.risk_history
      .map((w) => statusLabel(w.status === "checkin" ? "checkin" : w.status))
      .join(" → ");
  }
}

init();
