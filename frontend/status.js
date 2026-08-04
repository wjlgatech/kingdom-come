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

// A person reading their own page is not a case to be triaged. "At risk" is
// the director's word for a row in a list; said to someone's face it is a
// verdict. Same underlying score, same colour, honest either way — but the
// student's version ends in an invitation rather than a label.
export function statusLabelSelf(status) {
  switch (status) {
    case STATUS.THRIVING: return "In rhythm";
    case STATUS.STEADY: return "Steady";
    case STATUS.CHECK_IN: return "Worth a talk";
    case STATUS.AT_RISK: return "Let's talk";
    default: return "Unknown";
  }
}

const REASON_TRANSLATIONS = {
  low_engagement: () => "Engagement has dropped this week.",
  few_reflections: ({ days = 9 } = {}) => `Hasn't reflected in ${days} days.`,
  calling_drift: () => "Recent reflections lean away from earlier discernment.",
  missed_outcomes: ({ since = "three weeks" } = {}) => `Hasn't logged a ministry outcome in ${since}.`,
  high_engagement: () => "Reflecting consistently and engaged in cohort discussions.",
  frequent_reflections: () => "Reflecting most days this week.",
};

// Second person, for the page a student reads about themselves. Not a regex
// rewrite of the sentences above — a separate table, because "Hasn't reflected
// in 9 days" and "It's been 9 days since you last wrote" are different
// sentences, not the same sentence conjugated.
const REASON_TRANSLATIONS_SELF = {
  low_engagement: () => "You've been quieter here this week.",
  few_reflections: ({ days = 9 } = {}) => `It's been ${days} days since you last wrote anything down.`,
  calling_drift: () => "What you're writing now points somewhere different from where you started.",
  missed_outcomes: ({ since = "three weeks" } = {}) => `Nothing from ministry has gone in the log for ${since}.`,
  high_engagement: () => "You've shown up steadily this week.",
  frequent_reflections: () => "You've written most days this week.",
};

function translate(table, reasons, ctx, fallback) {
  if (!reasons || reasons.length === 0) return fallback;
  return reasons.map((code) => (table[code] ? table[code](ctx) : code)).join(" ");
}

export function reasonsToSentence(reasons, ctx = {}) {
  return translate(REASON_TRANSLATIONS, reasons, ctx, "Holding pattern this week.");
}

export function reasonsToSelfSentence(reasons, ctx = {}) {
  return translate(REASON_TRANSLATIONS_SELF, reasons, ctx, "A quiet week, nothing out of place.");
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
