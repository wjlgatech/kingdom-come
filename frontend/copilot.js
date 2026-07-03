// The Copilot door (agentic-portfolio pattern): ask the app about its own
// live data. Shared module — pages import { mountCopilot } and the role
// comes from document.body.dataset.role. The WS mirrors /ws/chat:
// {context: [...]} first (rendered as "Consulted:" pills), then chunks,
// then {done}.

function safeLs() { try { return window.localStorage; } catch { return null; } }

const STARTERS = {
  director: [
    "Who needs me this week, and why?",
    "How is the cohort's prayer rhythm?",
    "Where are we on the journey?",
  ],
  seminarian: [
    "How am I doing this week?",
    "What does my track record look like?",
    "What should I work on next?",
  ],
};

export function mountCopilot() {
  const role = document.body.dataset.role;
  if (!role) return;
  const studentId = safeLs()?.getItem("kc-student-id") ?? "";

  const trigger = document.createElement("button");
  trigger.type = "button";
  trigger.className = "copilot-trigger";
  trigger.dataset.testid = "copilot-trigger";
  trigger.setAttribute("aria-haspopup", "dialog");
  trigger.innerHTML = "Ask <em>✦</em>";
  document.body.appendChild(trigger);

  let panel = null;
  let socket = null;

  function ensureSocket() {
    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
      return socket;
    }
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    socket = new WebSocket(`${proto}//${window.location.host}/ws/copilot`);
    return socket;
  }

  function closePanel() {
    panel?.remove();
    panel = null;
    trigger.focus();
  }

  function ask(question) {
    const pills = panel.querySelector("[data-testid='copilot-pills']");
    const answer = panel.querySelector("[data-testid='copilot-answer']");
    pills.innerHTML = "";
    pills.hidden = true;
    answer.textContent = "•••";
    answer.dataset.state = "streaming";

    const ws = ensureSocket();
    let text = "";
    const onMessage = (ev) => {
      let msg;
      try { msg = JSON.parse(ev.data); } catch { return; }
      if (msg.error) {
        answer.textContent = msg.error;
        answer.dataset.state = "error";
        ws.removeEventListener("message", onMessage);
        return;
      }
      if (msg.context) {
        pills.hidden = false;
        const label = document.createElement("span");
        label.className = "label";
        label.textContent = "Consulted";
        pills.appendChild(label);
        msg.context.forEach((name) => {
          const pill = document.createElement("span");
          pill.className = "copilot-pill";
          pill.dataset.testid = "copilot-pill";
          pill.textContent = name;
          pills.appendChild(pill);
        });
        return;
      }
      if (msg.chunk !== undefined) {
        text += msg.chunk;
        answer.textContent = text;
        return;
      }
      if (msg.done) {
        answer.dataset.state = "done";
        ws.removeEventListener("message", onMessage);
      }
    };
    ws.addEventListener("message", onMessage);
    const payload = JSON.stringify({ role, question, student_id: studentId });
    if (ws.readyState === WebSocket.OPEN) ws.send(payload);
    else ws.addEventListener("open", () => ws.send(payload), { once: true });
  }

  function openPanel() {
    if (panel) return;
    panel = document.createElement("aside");
    panel.className = "copilot-panel";
    panel.dataset.testid = "copilot-panel";
    panel.setAttribute("role", "dialog");
    panel.setAttribute("aria-modal", "false");
    panel.setAttribute("aria-label", "Ask Kingdom Come");
    panel.innerHTML = `
      <div class="copilot-head">
        <h2 class="copilot-title">Ask <em>✦</em></h2>
        <button type="button" class="kc-modal-close" data-testid="copilot-close" aria-label="Close">×</button>
      </div>
      <p class="copilot-note">Answers come from your ${role === "director" ? "cohort's live signals — counts and statuses, never anyone's prayers" : "own record — nothing you haven't written"}.</p>
      <div class="copilot-starters" data-testid="copilot-starters"></div>
      <form class="copilot-form" data-testid="copilot-form">
        <label for="copilot-q" class="visually-hidden">Your question</label>
        <input id="copilot-q" type="text" placeholder="Ask about this week…" autocomplete="off" />
        <button type="submit" class="btn btn-primary" data-testid="copilot-send">Ask</button>
      </form>
      <div class="copilot-pills" data-testid="copilot-pills" hidden></div>
      <p class="copilot-answer" data-testid="copilot-answer" aria-live="polite"></p>
    `;
    document.body.appendChild(panel);

    const starters = panel.querySelector("[data-testid='copilot-starters']");
    (STARTERS[role] ?? []).forEach((q) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "copilot-starter";
      b.dataset.testid = "copilot-starter";
      b.textContent = q;
      b.addEventListener("click", () => {
        panel.querySelector("#copilot-q").value = q;
        ask(q);
      });
      starters.appendChild(b);
    });

    panel.querySelector("[data-testid='copilot-close']").addEventListener("click", closePanel);
    panel.addEventListener("keydown", (e) => { if (e.key === "Escape") closePanel(); });
    panel.querySelector("[data-testid='copilot-form']").addEventListener("submit", (e) => {
      e.preventDefault();
      const q = panel.querySelector("#copilot-q").value.trim();
      if (q) ask(q);
    });
    panel.querySelector("#copilot-q").focus();
  }

  trigger.addEventListener("click", () => (panel ? closePanel() : openPanel()));
}
