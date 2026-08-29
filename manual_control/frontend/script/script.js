// manual_control/frontend/script/script.js
// ─────────────────────────────────────────
// Sends rover commands to the Flask backend and manages UI state.

const badge = document.getElementById("status-badge");

/**
 * Send a command to the Flask /control endpoint.
 * @param {string} command  - 'forward' | 'backward' | 'left' | 'right' | 'stop'
 * @param {string} action   - 'start' | 'stop'
 */
async function send(command, action) {
  try {
    await fetch("/control", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command, action }),
    });
    updateBadge(command, action);
  } catch (err) {
    console.error("Control error:", err);
  }
}

function updateBadge(command, action) {
  if (command === "stop" || action === "stop") {
    badge.textContent = "● Stopped";
    badge.className   = "badge badge-stopped";
  } else {
    const labels = { forward: "▲ Forward", backward: "▼ Backward", left: "◀ Left", right: "▶ Right" };
    badge.textContent = labels[command] || "● Moving";
    badge.className   = "badge badge-moving";
  }
}

// ── Keyboard bindings ─────────────────────────────────────────────────────────
const KEY_MAP = {
  ArrowUp:    "forward",  w: "forward",
  ArrowDown:  "backward", s: "backward",
  ArrowLeft:  "left",     a: "left",
  ArrowRight: "right",    d: "right",
  " ":        "stop",
};
const _pressed = new Set();

document.addEventListener("keydown", (e) => {
  const cmd = KEY_MAP[e.key];
  if (!cmd || _pressed.has(cmd)) return;
  _pressed.add(cmd);
  send(cmd, cmd === "stop" ? "start" : "start");

  // Visual feedback on D-pad buttons
  const btnId = `btn-${cmd}`;
  const btn   = document.getElementById(btnId);
  if (btn) btn.classList.add("pressed");
});

document.addEventListener("keyup", (e) => {
  const cmd = KEY_MAP[e.key];
  if (!cmd) return;
  _pressed.delete(cmd);
  if (cmd !== "stop") send(cmd, "stop");

  const btn = document.getElementById(`btn-${cmd}`);
  if (btn) btn.classList.remove("pressed");
});

// ── Prevent context menu on long-press (mobile) ───────────────────────────────
document.querySelectorAll(".dpad-btn").forEach((btn) => {
  btn.addEventListener("contextmenu", (e) => e.preventDefault());
});
