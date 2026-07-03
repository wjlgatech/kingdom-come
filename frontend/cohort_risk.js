// Shared client-side scoring path: every surface that needs a student's
// risk (triage rows, the door's director preview) goes through the same
// backend call + override weighting, so no two surfaces can disagree.
import { STATUS, statusFromRisk } from "/static/status.js";

export async function scoreStudent(student) {
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

export function countFlagged(scored) {
  return scored.filter((s) => {
    const status = statusFromRisk({ score: s.data?.score ?? 0 });
    return status === STATUS.AT_RISK || status === STATUS.CHECK_IN;
  }).length;
}
