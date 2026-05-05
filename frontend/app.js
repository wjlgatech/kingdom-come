const asJson = (value) => JSON.stringify(value, null, 2);

async function postJson(path, payload) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    const detail = Array.isArray(data.detail)
      ? data.detail.map((item) => item.msg).join("; ")
      : data.detail || "Request failed";
    throw new Error(detail);
  }
  return data;
}

function writeResult(target, payload, isError = false) {
  target.textContent = isError ? payload : asJson(payload);
  target.classList.toggle("error", isError);
}

function parseCsv(value) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function parseGroups(value) {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, index) => {
      const [rawId, rawMembers = ""] = line.includes(":") ? line.split(":") : [`group-${index + 1}`, line];
      return { id: rawId.trim(), members: parseCsv(rawMembers) };
    });
}

async function submitDropoutRisk(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const output = document.querySelector("#risk-result");
  const payload = {
    engagement: Number(form.engagement.value),
    reflection_count: Number(form.reflection_count.value),
  };
  try {
    writeResult(output, await postJson("/predictive/dropout-risk", payload));
  } catch (error) {
    writeResult(output, error.message, true);
  }
}

async function submitCurriculum(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const output = document.querySelector("#curriculum-result");
  const payload = {
    calling: form.calling.value,
    completed_content: parseCsv(form.completed_content.value),
  };
  try {
    writeResult(output, await postJson("/curriculum/recommendations", payload));
  } catch (error) {
    writeResult(output, error.message, true);
  }
}

async function submitOrchestration(event) {
  event.preventDefault();
  const output = document.querySelector("#orchestration-result");
  try {
    writeResult(output, await postJson("/orchestration/actions", parseGroups(event.currentTarget.groups.value)));
  } catch (error) {
    writeResult(output, error.message, true);
  }
}

async function submitOutcome(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const output = document.querySelector("#outcome-result");
  const payload = {
    student_id: form.student_id.value,
    impact_score: Number(form.impact_score.value),
    description: form.description.value,
  };
  try {
    writeResult(output, await postJson("/outcomes", payload));
  } catch (error) {
    writeResult(output, error.message, true);
  }
}

document.querySelector("#dropout-form").addEventListener("submit", submitDropoutRisk);
document.querySelector("#curriculum-form").addEventListener("submit", submitCurriculum);
document.querySelector("#orchestration-form").addEventListener("submit", submitOrchestration);
document.querySelector("#outcome-form").addEventListener("submit", submitOutcome);
