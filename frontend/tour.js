// First-run tour (REC onboarding, anti-pattern AP4: the product explains
// itself, no external "how to" page). A quiet three-step card at the top of
// the page — not a spotlight overlay; Editorial Pastoral keeps chrome calm.
// Dismissal persists per surface in localStorage (`kc-tour-<key>`).

function safeLs() { try { return window.localStorage; } catch { return null; } }

export function mountTour(key, steps) {
  const ls = safeLs();
  const storageKey = `kc-tour-${key}`;
  if (!ls || ls.getItem(storageKey) === "done" || steps.length === 0) return;

  const main = document.querySelector("main");
  if (!main) return;

  const card = document.createElement("aside");
  card.className = "kc-tour";
  card.dataset.testid = "kc-tour";
  card.setAttribute("aria-label", "First-time tour");

  const label = document.createElement("p");
  label.className = "kc-tour-label";
  label.textContent = "First time here?";
  card.appendChild(label);

  const title = document.createElement("h2");
  title.className = "kc-tour-title";
  title.dataset.testid = "kc-tour-title";
  const body = document.createElement("p");
  body.className = "kc-tour-body";
  card.appendChild(title);
  card.appendChild(body);

  const footer = document.createElement("div");
  footer.className = "kc-tour-footer";
  const dots = document.createElement("span");
  dots.className = "kc-tour-dots";
  dots.setAttribute("aria-hidden", "true");
  const skip = document.createElement("button");
  skip.type = "button";
  skip.className = "btn btn-ghost inline";
  skip.dataset.testid = "kc-tour-skip";
  skip.textContent = "Skip";
  const next = document.createElement("button");
  next.type = "button";
  next.className = "btn btn-secondary";
  next.dataset.testid = "kc-tour-next";
  footer.appendChild(dots);
  footer.appendChild(skip);
  footer.appendChild(next);
  card.appendChild(footer);

  let idx = 0;
  function render() {
    const step = steps[idx];
    title.textContent = step.title;
    body.textContent = step.body;
    next.textContent = idx === steps.length - 1 ? "Done" : "Next →";
    dots.textContent = steps.map((_, i) => (i === idx ? "●" : "○")).join(" ");
  }

  function finish() {
    try { ls.setItem(storageKey, "done"); } catch { /* private browsing */ }
    card.remove();
  }

  next.addEventListener("click", () => {
    if (idx === steps.length - 1) { finish(); return; }
    idx += 1;
    render();
  });
  skip.addEventListener("click", finish);

  render();
  main.insertBefore(card, main.firstChild);
}
