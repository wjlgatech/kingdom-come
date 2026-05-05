// P1 demo cohort. Replace with fetch('/cohort/students') when the real
// endpoint lands; the consumer interface stays identical.

export const DEMO_DIRECTOR = Object.freeze({
  id: "fd-theresa",
  name: "Sister Theresa Marquez",
  cohort_id: "st-aloysius-s26",
  cohort_name: "St. Aloysius cohort, Spring 2026",
});

export const DEMO_SEMINARIAN_ID = "stu-marcus-r";

export const COHORT = [
  // High-stake row 1: Marcus — needs check-in (score 2: low_engagement + few_reflections)
  { id: "stu-marcus-r", name: "Marcus Reilly",   engagement: 0.25, reflection_count: 1, calling: ["evangelism"],     reason_overrides: { few_reflections: { days: 9 } } },
  // At-risk: Sarah — backend score 3, calling drift override pushes higher
  { id: "stu-sarah-k",  name: "Sarah Kim",       engagement: 0.18, reflection_count: 0, calling: ["liturgy"],         reason_overrides: { calling_drift: {} } },
  // Needs check-in: David — engagement softening only (score 2: low_engagement + reflections OK)
  { id: "stu-david-o",  name: "David Okafor",    engagement: 0.28, reflection_count: 3, calling: ["pastoral_care"] },
  // Thriving: Anna
  { id: "stu-anna-t",   name: "Anna Theroux",    engagement: 0.85, reflection_count: 4, calling: ["mission"] },
  // Steady cohort filler — 20 more for a realistic 24-student feel
  { id: "stu-luca-b",   name: "Luca Benedict",   engagement: 0.62, reflection_count: 3, calling: ["mission"] },
  { id: "stu-grace-w",  name: "Grace Winters",   engagement: 0.71, reflection_count: 3, calling: ["evangelism"] },
  { id: "stu-jonas-r",  name: "Jonas Reuter",    engagement: 0.58, reflection_count: 2, calling: ["liturgy"] },
  { id: "stu-eli-p",    name: "Eli Patel",       engagement: 0.66, reflection_count: 3, calling: ["pastoral_care"] },
  { id: "stu-noor-h",   name: "Noor Habib",      engagement: 0.74, reflection_count: 3, calling: ["mission"] },
  { id: "stu-leo-c",    name: "Leo Castellano",  engagement: 0.55, reflection_count: 2, calling: ["evangelism"] },
  { id: "stu-isabel-m", name: "Isabel Marín",    engagement: 0.83, reflection_count: 4, calling: ["liturgy"] },
  { id: "stu-pius-n",   name: "Pius Nwosu",      engagement: 0.69, reflection_count: 3, calling: ["pastoral_care"] },
  { id: "stu-maria-l",  name: "Maria Lefevre",   engagement: 0.61, reflection_count: 2, calling: ["mission"] },
  { id: "stu-tomas-v",  name: "Tomás Vega",      engagement: 0.77, reflection_count: 3, calling: ["evangelism"] },
  { id: "stu-rachel-y", name: "Rachel Yoon",     engagement: 0.72, reflection_count: 3, calling: ["liturgy"] },
  { id: "stu-james-o",  name: "James O'Neill",   engagement: 0.68, reflection_count: 3, calling: ["pastoral_care"] },
  { id: "stu-clare-d",  name: "Clare Donovan",   engagement: 0.59, reflection_count: 2, calling: ["evangelism"] },
  { id: "stu-andrew-j", name: "Andrew Johansson",engagement: 0.81, reflection_count: 4, calling: ["mission"] },
  { id: "stu-bea-s",    name: "Bea Solano",      engagement: 0.56, reflection_count: 2, calling: ["liturgy"] },
  { id: "stu-malik-a",  name: "Malik Adekunle",  engagement: 0.73, reflection_count: 3, calling: ["pastoral_care"] },
  { id: "stu-simone-c", name: "Simone Chen",     engagement: 0.65, reflection_count: 3, calling: ["mission"] },
  { id: "stu-paul-z",   name: "Paul Zoller",     engagement: 0.79, reflection_count: 4, calling: ["evangelism"] },
  { id: "stu-rosa-i",   name: "Rosa Iglesias",   engagement: 0.84, reflection_count: 4, calling: ["liturgy"] },
  { id: "stu-finn-h",   name: "Finn Hartigan",   engagement: 0.88, reflection_count: 5, calling: ["pastoral_care"] },
];

export function findStudent(id) {
  return COHORT.find((s) => s.id === id) ?? null;
}

// Per-student profile fixtures. Plain placeholder content — replace with
// fetched data when the profile aggregation endpoint exists.
export const PROFILE_FIXTURES = {
  "stu-marcus-r": {
    reflections: [
      { date: "2026-04-29", excerpt: "The small group felt heavy this week. Sister Theresa would say to bring it to prayer." },
      { date: "2026-04-22", excerpt: "Mission Theology is harder than I thought. I'm not sure I'm reading it the right way." },
      { date: "2026-04-15", excerpt: "Led morning prayer for the first time. Hands shaking, but I did it." },
    ],
    outcomes: [],
    risk_history: [
      { week: "Week 1", status: "thriving" },
      { week: "Week 2", status: "thriving" },
      { week: "Week 3", status: "steady" },
      { week: "Week 4", status: "steady" },
      { week: "Week 5", status: "checkin" },
      { week: "Week 6", status: "checkin" },
      { week: "Week 7", status: "checkin" },
    ],
  },
  "stu-sarah-k": {
    reflections: [
      { date: "2026-04-30", excerpt: "I keep coming back to the question of whether I'm here for the right reasons." },
      { date: "2026-04-23", excerpt: "Liturgy class moved me this week. The Eucharist as the source and summit." },
    ],
    outcomes: [],
    risk_history: [
      { week: "Week 1", status: "thriving" }, { week: "Week 2", status: "steady" },
      { week: "Week 3", status: "steady" }, { week: "Week 4", status: "checkin" },
      { week: "Week 5", status: "checkin" }, { week: "Week 6", status: "risk" },
      { week: "Week 7", status: "risk" },
    ],
  },
  "stu-david-o": {
    reflections: [
      { date: "2026-04-28", excerpt: "Spring break visit home was harder than expected. Father is sick." },
    ],
    outcomes: [
      { date: "2026-03-21", student_id: "stu-david-o", impact_score: 0.75, description: "Led the parish youth retreat preparation team.", effectiveness: "strong" },
    ],
    risk_history: [
      { week: "Week 1", status: "thriving" }, { week: "Week 2", status: "thriving" },
      { week: "Week 3", status: "steady" }, { week: "Week 4", status: "steady" },
      { week: "Week 5", status: "steady" }, { week: "Week 6", status: "checkin" },
      { week: "Week 7", status: "checkin" },
    ],
  },
  "stu-anna-t": {
    reflections: [
      { date: "2026-05-01", excerpt: "The parish council has invited me to lead next month's catechesis. I said yes." },
      { date: "2026-04-24", excerpt: "Three days of silent retreat. I needed it more than I knew." },
    ],
    outcomes: [
      { date: "2026-04-18", student_id: "stu-anna-t", impact_score: 0.86, description: "Led a supervised neighborhood cohort.", effectiveness: "strong" },
      { date: "2026-03-30", student_id: "stu-anna-t", impact_score: 0.72, description: "Coordinated parish soup kitchen volunteers for Holy Week.", effectiveness: "developing" },
    ],
    risk_history: [
      { week: "Week 1", status: "steady" }, { week: "Week 2", status: "thriving" },
      { week: "Week 3", status: "thriving" }, { week: "Week 4", status: "thriving" },
      { week: "Week 5", status: "thriving" }, { week: "Week 6", status: "thriving" },
      { week: "Week 7", status: "thriving" },
    ],
  },
};

export function getProfile(id) {
  return PROFILE_FIXTURES[id] ?? { reflections: [], outcomes: [], risk_history: [] };
}
