// Single source of truth for status thresholds, reason translation,
// and avatar derivation. Loaded via <script type="module">.

export const STATUS = Object.freeze({
  THRIVING: "thriving",
  STEADY: "steady",
  CHECK_IN: "checkin",
  AT_RISK: "risk",
});

export function statusFromRisk({ score = 0 } = {}) {
  if (score >= 3) return STATUS.AT_RISK;
  if (score === 2) return STATUS.CHECK_IN;
  if (score === 1) return STATUS.STEADY;
  return STATUS.THRIVING;
}

export function statusLabel(status) {
  switch (status) {
    case STATUS.THRIVING: return "Thriving";
    case STATUS.STEADY: return "Steady";
    case STATUS.CHECK_IN: return "Needs check-in";
    case STATUS.AT_RISK: return "At risk";
    default: return "Unknown";
  }
}

export function statusClass(status) {
  return `status-${status}`;
}

const REASON_TRANSLATIONS = {
  low_engagement: () => "Engagement has dropped this week.",
  few_reflections: ({ days = 9 } = {}) => `Hasn't reflected in ${days} days.`,
  calling_drift: () => "Recent reflections lean away from earlier discernment.",
  missed_outcomes: ({ since = "three weeks" } = {}) => `Hasn't logged a ministry outcome in ${since}.`,
  high_engagement: () => "Reflecting consistently and engaged in cohort discussions.",
  frequent_reflections: () => "Reflecting most days this week.",
};

export function reasonsToSentence(reasons, ctx = {}) {
  if (!reasons || reasons.length === 0) return "Holding pattern this week.";
  return reasons
    .map((code) => {
      const translator = REASON_TRANSLATIONS[code];
      return translator ? translator(ctx) : code;
    })
    .join(" ");
}

const AVATAR_PALETTE_LIGHTNESS = 88;
const AVATAR_PALETTE_SATURATION = 35;

export function avatarHue(name) {
  if (!name) return 0;
  return [...name].reduce((h, c) => h + c.charCodeAt(0), 0) % 360;
}

export function avatarBackground(name) {
  return `hsl(${avatarHue(name)}, ${AVATAR_PALETTE_SATURATION}%, ${AVATAR_PALETTE_LIGHTNESS}%)`;
}

export function avatarInitials(name) {
  if (!name) return "??";
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0] || "")
    .join("")
    .toUpperCase();
}

// Helper: construct an avatar element from a name.
export function avatarElement(name, size = "default") {
  const el = document.createElement("span");
  el.className = size === "sm" ? "avatar sm" : "avatar";
  el.style.background = avatarBackground(name);
  el.textContent = avatarInitials(name);
  el.setAttribute("aria-hidden", "true");
  return el;
}
