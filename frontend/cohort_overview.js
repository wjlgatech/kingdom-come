import { COHORT } from "/static/cohort_data.js";
import { STATUS, statusFromRisk, statusLabel, statusClass, reasonsToSentence, avatarBackground, avatarInitials } from "/static/status.js";

const STATUS_PRIORITY = { [STATUS.AT_RISK]: 0, [STATUS.CHECK_IN]: 1, [STATUS.STEADY]: 2, [STATUS.THRIVING]: 3 };

// 8-week median engagement trend, derived from a deterministic walk down to
// today's actual cohort median. P1 fixture; replace with backend aggregation
// when historical data lands.
function buildEngagementTrend() {
  const todayMedian = median(COHORT.map((s) => s.engagement));
  // Trend rises early, dips during weeks 4-5 (mock spring break), then partially recovers.
  // Anchored so the last point matches today's actual median.
  const profile = [0.78, 0.74, 0.72, 0.65, 0.58, 0.61, 0.64, todayMedian];
  return profile.map((v, i) => ({ week: i + 1, value: v }));
}

function median(arr) {
  const sorted = [...arr].sort((a, b) => a - b);
  const m = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[m] : (sorted[m - 1] + sorted[m]) / 2;
}

function renderChart(points) {
  const fig = document.querySelector("[data-testid='cohort-chart']");
  fig.innerHTML = "";
  const W = 720, H = 200, padX = 32, padY = 20;
  const innerW = W - 2 * padX, innerH = H - 2 * padY;
  const xs = points.map((_, i) => padX + (innerW * i) / (points.length - 1));
  const ys = points.map((p) => padY + innerH - (innerH * p.value));

  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", "Cohort median engagement over the last eight weeks");
  svg.dataset.testid = "cohort-chart-svg";

  // Grid lines at 0.25, 0.5, 0.75
  [0.25, 0.5, 0.75].forEach((g) => {
    const y = padY + innerH - innerH * g;
    const line = document.createElementNS(ns, "line");
    line.setAttribute("x1", padX); line.setAttribute("x2", W - padX);
    line.setAttribute("y1", y); line.setAttribute("y2", y);
    line.setAttribute("class", "grid");
    svg.appendChild(line);
    const lbl = document.createElementNS(ns, "text");
    lbl.setAttribute("x", 4); lbl.setAttribute("y", y + 4);
    lbl.setAttribute("class", "axis-label");
    lbl.textContent = g.toFixed(2);
    svg.appendChild(lbl);
  });

  // Area
  const areaPath = `M ${xs[0]} ${padY + innerH} ${xs.map((x, i) => `L ${x} ${ys[i]}`).join(" ")} L ${xs[xs.length - 1]} ${padY + innerH} Z`;
  const area = document.createElementNS(ns, "path");
  area.setAttribute("d", areaPath);
  area.setAttribute("class", "area");
  svg.appendChild(area);

  // Line
  const linePath = `M ${xs[0]} ${ys[0]} ${xs.slice(1).map((x, i) => `L ${x} ${ys[i + 1]}`).join(" ")}`;
  const line = document.createElementNS(ns, "path");
  line.setAttribute("d", linePath);
  line.setAttribute("class", "line");
  svg.appendChild(line);

  // Points + week labels
  points.forEach((p, i) => {
    const c = document.createElementNS(ns, "circle");
    c.setAttribute("cx", xs[i]); c.setAttribute("cy", ys[i]);
    c.setAttribute("r", 4);
    c.setAttribute("class", "point");
    svg.appendChild(c);
    if (i === 0 || i === points.length - 1 || (i + 1) % 2 === 0) {
      const lbl = document.createElementNS(ns, "text");
      lbl.setAttribute("x", xs[i]); lbl.setAttribute("y", H - 4);
      lbl.setAttribute("text-anchor", "middle");
      lbl.setAttribute("class", "axis-label");
      lbl.textContent = `W${p.week}`;
      svg.appendChild(lbl);
    }
  });

  fig.appendChild(svg);
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

function reasonContext(student, reasons) {
  if (!reasons || reasons.length === 0) return {};
  const overrides = student.reason_overrides ?? {};
  return overrides[reasons[0]] ?? {};
}

function renderSnippet(scored) {
  const list = document.querySelector("[data-testid='cohort-snippet-list']");
  list.removeAttribute("aria-busy");
  list.innerHTML = "";
  const flagged = scored
    .filter((s) => {
      const st = statusFromRisk({ score: s.data?.score ?? 0 });
      return st === STATUS.AT_RISK || st === STATUS.CHECK_IN;
    })
    .sort((a, b) => {
      const sa = statusFromRisk({ score: a.data?.score ?? 0 });
      const sb = statusFromRisk({ score: b.data?.score ?? 0 });
      return STATUS_PRIORITY[sa] - STATUS_PRIORITY[sb];
    })
    .slice(0, 3);

  if (flagged.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.dataset.testid = "cohort-snippet-empty";
    empty.textContent = "No one needs a check-in this week. The cohort is steady.";
    list.appendChild(empty);
    return;
  }

  flagged.forEach(({ student, data }) => {
    const status = statusFromRisk({ score: data.score });
    const row = document.createElement("a");
    row.href = `/students/${student.id}`;
    row.className = "cohort-snippet-row";
    row.dataset.testid = "cohort-snippet-row";
    const av = document.createElement("span");
    av.className = "avatar sm";
    av.style.background = avatarBackground(student.name);
    av.textContent = avatarInitials(student.name);
    av.setAttribute("aria-hidden", "true");
    row.appendChild(av);
    const content = document.createElement("div");
    const name = document.createElement("div");
    name.className = "cohort-snippet-name";
    name.textContent = student.name;
    const reason = document.createElement("div");
    reason.className = "cohort-snippet-reason";
    reason.textContent = reasonsToSentence(data.reasons ?? [], reasonContext(student, data.reasons));
    content.appendChild(name);
    content.appendChild(reason);
    row.appendChild(content);
    const pill = document.createElement("span");
    pill.className = `status-pill ${statusClass(status)}`;
    pill.textContent = statusLabel(status);
    row.appendChild(pill);
    list.appendChild(row);
  });
}

async function init() {
  // Chart is synthetic — render immediately.
  renderChart(buildEngagementTrend());

  // Score every student, then summary + snippet.
  const scored = await Promise.all(COHORT.map(scoreStudent));
  const flaggedCount = scored.filter((s) => {
    const st = statusFromRisk({ score: s.data?.score ?? 0 });
    return st === STATUS.AT_RISK || st === STATUS.CHECK_IN;
  }).length;
  const thrivingCount = scored.filter(
    (s) => statusFromRisk({ score: s.data?.score ?? 0 }) === STATUS.THRIVING,
  ).length;

  const sentence = (() => {
    if (flaggedCount === 0) return `All ${COHORT.length} students are holding steady this week. Spend the time you'd have spent triaging on a thriving student you haven't talked to in a while.`;
    if (flaggedCount <= 3) return `${flaggedCount} of ${COHORT.length} students need attention this week. ${thrivingCount} are thriving. Open triage to start where it matters.`;
    return `${flaggedCount} of ${COHORT.length} students need attention this week. The cohort's median engagement has softened — a touch-base round may be worth your hour.`;
  })();

  const para = document.querySelector("[data-testid='cohort-paragraph']");
  para.textContent = sentence;

  renderSnippet(scored);
}

init();
