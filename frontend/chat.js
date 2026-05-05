function safeLs() { try { return window.localStorage; } catch { return null; } }

const ls = safeLs();
const studentId = ls?.getItem("kc-student-id") ?? "stu-marcus-r";

const thread = document.querySelector("[data-testid='chat-thread']");
const memoryPills = document.querySelector("[data-testid='memory-pills']");
const status = document.querySelector("[data-testid='chat-conn-status']");
const form = document.querySelector("[data-testid='chat-form']");
const messageInput = document.querySelector("[data-testid='chat-message-input']");

let socket = null;
let pendingMentorBubble = null;
let pendingMentorText = "";

function setStatus(state, label) {
  if (!status) return;
  status.dataset.state = state;
  status.textContent = label;
}

function renderMemoryPills(memory) {
  if (!memoryPills) return;
  // Clear existing pill children but keep the label.
  memoryPills.querySelectorAll(".memory-pill").forEach((el) => el.remove());
  if (!memory || memory.length === 0) {
    memoryPills.hidden = true;
    return;
  }
  memoryPills.hidden = false;
  memory.slice(0, 3).forEach((snippet) => {
    const pill = document.createElement("span");
    pill.className = "memory-pill";
    pill.dataset.testid = "memory-pill";
    pill.title = snippet;
    pill.textContent = snippet.length > 40 ? `${snippet.slice(0, 40)}…` : snippet;
    pill.setAttribute("aria-label", `Mentor remembers: ${snippet}`);
    memoryPills.appendChild(pill);
  });
}

function appendStudentBubble(text) {
  const bubble = document.createElement("div");
  bubble.className = "bubble student";
  bubble.dataset.testid = "chat-bubble-student";
  bubble.textContent = text;
  thread.appendChild(bubble);
  thread.scrollTop = thread.scrollHeight;
}

function startMentorBubble() {
  pendingMentorText = "";
  pendingMentorBubble = document.createElement("div");
  pendingMentorBubble.className = "bubble mentor";
  pendingMentorBubble.dataset.testid = "chat-bubble-mentor";
  pendingMentorBubble.textContent = "•••";
  thread.appendChild(pendingMentorBubble);
  thread.scrollTop = thread.scrollHeight;
}

function appendMentorChunk(chunk) {
  if (!pendingMentorBubble) startMentorBubble();
  pendingMentorText += chunk;
  pendingMentorBubble.textContent = pendingMentorText;
  thread.scrollTop = thread.scrollHeight;
}

function finalizeMentorBubble() {
  if (pendingMentorBubble && !pendingMentorText.trim()) {
    pendingMentorBubble.textContent = "(no response)";
  }
  pendingMentorBubble = null;
  pendingMentorText = "";
}

function showError(text) {
  finalizeMentorBubble();
  const bubble = document.createElement("div");
  bubble.className = "bubble error";
  bubble.dataset.testid = "chat-bubble-error";
  bubble.textContent = text;
  thread.appendChild(bubble);
  thread.scrollTop = thread.scrollHeight;
}

function ensureSocket() {
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
    return socket;
  }
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  socket = new WebSocket(`${proto}//${window.location.host}/ws/chat`);
  setStatus("connecting", "connecting…");
  socket.addEventListener("open", () => setStatus("connected", "connected"));
  socket.addEventListener("close", () => setStatus("reconnecting", "reconnecting…"));
  socket.addEventListener("error", () => setStatus("error", "error"));
  socket.addEventListener("message", (ev) => {
    let parsed;
    try { parsed = JSON.parse(ev.data); } catch { return; }
    if (parsed.error) {
      showError("I'm not able to think clearly just now. Try again in a moment.");
      setStatus("ready", "ready");
      return;
    }
    if (parsed.memory !== undefined) {
      renderMemoryPills(parsed.memory);
      return;
    }
    if (parsed.chunk !== undefined) {
      if (!pendingMentorBubble) startMentorBubble();
      appendMentorChunk(parsed.chunk);
      return;
    }
    if (parsed.done) {
      finalizeMentorBubble();
      setStatus("ready", "ready");
    }
  });
  return socket;
}

function sendMessage() {
  const text = messageInput.value.trim();
  if (!text) return;
  appendStudentBubble(text);
  messageInput.value = "";
  startMentorBubble();
  const ws = ensureSocket();
  const payload = JSON.stringify({ student_id: studentId, message: text });
  if (ws.readyState === WebSocket.OPEN) ws.send(payload);
  else ws.addEventListener("open", () => ws.send(payload), { once: true });
}

form.addEventListener("submit", (e) => { e.preventDefault(); sendMessage(); });
messageInput.addEventListener("keydown", (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
    e.preventDefault();
    sendMessage();
  }
});

// Auto-focus input on load.
messageInput.focus();
