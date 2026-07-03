// Voice input — the dreammaketrue /voice stack: tap the mic to record
// (MediaRecorder), tap again to stop; one POST to /api/voice/transcribe and
// the text lands in the input. The mic only mounts when the server's health
// probe says a transcription tier is live (a dead mic is worse than none),
// and the silence diagnostics mirror the reference implementation: opus
// compresses silence to ~1KB/s, so a low KB/s ratio means the mic recorded
// nothing (usually the wrong input device), not that the user spoke softly.

export async function mountVoiceInput(input, { onText, onNote } = {}) {
  if (!input) return null;
  try {
    const health = await (await fetch("/api/voice/health")).json();
    if (!health.available) return null;
  } catch {
    return null;
  }

  const mic = document.createElement("button");
  mic.type = "button";
  mic.className = "voice-mic";
  mic.dataset.testid = "voice-mic";
  mic.setAttribute("aria-label", "Speak instead of typing");
  mic.textContent = "🎙";
  input.insertAdjacentElement("afterend", mic);

  const note = (text) => (onNote ?? (() => {}))(text);
  let rec = null;
  let stream = null;
  let chunks = [];
  let startedAt = 0;

  mic.addEventListener("click", async () => {
    if (rec) { rec.stop(); return; }
    if (!navigator.mediaDevices?.getUserMedia) {
      note("Voice needs HTTPS or localhost — this page can't reach the microphone.");
      return;
    }
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      note(`Microphone permission denied: ${err.message}`);
      return;
    }
    const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
      ? "audio/webm;codecs=opus"
      : (MediaRecorder.isTypeSupported("audio/mp4") ? "audio/mp4" : "");
    rec = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
    chunks = [];
    rec.ondataavailable = (e) => { if (e.data.size) chunks.push(e.data); };
    rec.onstop = async () => {
      mic.classList.remove("rec");
      mic.textContent = "🎙";
      stream.getTracks().forEach((t) => t.stop());
      stream = null;
      const blob = new Blob(chunks, { type: rec.mimeType || "audio/webm" });
      rec = null;
      const secs = (Date.now() - startedAt) / 1000;
      if (blob.size < 2048) {
        note("Heard nothing — tap, speak a full sentence, tap again.");
        return;
      }
      const prevPlaceholder = input.placeholder;
      input.placeholder = "transcribing…";
      mic.disabled = true;
      try {
        const res = await fetch("/api/voice/transcribe", {
          method: "POST",
          headers: { "Content-Type": blob.type || "audio/webm" },
          body: blob,
        });
        const out = res.ok ? await res.json() : {};
        if (out.text) {
          input.value = out.text;
          input.dispatchEvent(new Event("input", { bubbles: true }));
          (onText ?? (() => {}))(out.text);
        } else {
          const rate = blob.size / 1024 / Math.max(1, secs);
          note(rate < 3
            ? "The recording was silent — check the mic the browser picked (address-bar 🎙 icon)."
            : "No words recognized — try a full sentence.");
        }
      } catch (err) {
        note(`Transcription failed: ${err.message}`);
      } finally {
        input.placeholder = prevPlaceholder;
        mic.disabled = false;
        input.focus();
      }
    };
    startedAt = Date.now();
    rec.start(250);
    mic.classList.add("rec");
    mic.textContent = "⏹";
  });
  return mic;
}
