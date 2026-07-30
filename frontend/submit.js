// Student submission portal — one POST, an honest receipt back.

const $ = (sel) => document.querySelector(sel);

async function loadDeadline() {
  try {
    const { deadline } = await (await fetch("/api/grading/submissions")).json();
    const due = new Date(deadline);
    const line = $('[data-testid="deadline-line"]');
    const fmt = due.toLocaleString("zh-CN", { dateStyle: "full", timeStyle: "short" });
    if (Date.now() > due.getTime()) {
      line.textContent = `截止时间已过（${fmt}）——仍可提交，由陈老师酌情处理。`;
      line.classList.add("late");
    } else {
      const days = Math.floor((due.getTime() - Date.now()) / 86400000);
      line.textContent = `截止时间：${fmt}（还剩 ${days} 天）`;
    }
  } catch { /* keep the static fallback text */ }
}

$('[data-testid="submit-form"]').addEventListener("submit", async (e) => {
  e.preventDefault();
  const status = $('[data-testid="status-line"]');
  const fileInput = $('[data-testid="file-input"]');
  const file = fileInput.files[0];
  if (!file) { status.textContent = "请先选择你的 PDF 报告文件。"; return; }

  const form = new FormData();
  form.append("file", file);
  form.append("consent", $('[data-testid="consent-check"]').checked ? "yes" : "no");

  status.textContent = "";
  $('[data-testid="submit-btn"]').disabled = true;
  try {
    const res = await fetch("/api/grading/submissions", { method: "POST", body: form });
    const body = await res.json();
    if (!res.ok) throw new Error(body.detail || res.statusText);

    const box = $('[data-testid="receipt"]');
    box.hidden = false;
    box.innerHTML = "";
    const ok = document.createElement("div");
    ok.textContent = `✓ 已收到：${body.filename}（${new Date(body.received_at).toLocaleString("zh-CN")}）`;
    box.appendChild(ok);
    for (const w of body.warnings) {
      const el = document.createElement("span");
      el.className = "receipt-warning";
      el.textContent = "⚠ " + w;
      box.appendChild(el);
    }
    fileInput.value = "";
  } catch (err) {
    status.textContent = err.message;
  } finally {
    $('[data-testid="submit-btn"]').disabled = false;
  }
});

loadDeadline();
