// Cohort data, fetched from the backend fixtures via /api/students so the
// frontend and the agent-facing API share one source of truth
// (backend/fixtures/cohort.py). Uses top-level await — every consumer
// imports this as an ES module, so pages render once the roster resolves.
// On fetch failure COHORT is empty and each surface shows its own
// error/empty state instead of a broken page.

export const DEMO_DIRECTOR = Object.freeze({
  id: "fd-theresa",
  name: "Sister Theresa Marquez",
  cohort_id: "st-aloysius-s26",
  cohort_name: "St. Aloysius cohort, Spring 2026",
});

export const DEMO_SEMINARIAN_ID = "stu-marcus-r";

async function fetchCohort() {
  try {
    const res = await fetch("/api/students");
    if (!res.ok) return [];
    const data = await res.json();
    return data.students ?? [];
  } catch {
    return [];
  }
}

export const COHORT = await fetchCohort();

export function findStudent(id) {
  return COHORT.find((s) => s.id === id) ?? null;
}

// Per-student profile feed (reflections / outcomes / risk history), served
// by /api/students/{id}. Async — callers await it.
export async function getProfile(id) {
  try {
    const res = await fetch(`/api/students/${id}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return {
      reflections: data.reflections ?? [],
      outcomes: data.outcomes ?? [],
      risk_history: data.risk_history ?? [],
    };
  } catch {
    return { reflections: [], outcomes: [], risk_history: [] };
  }
}
