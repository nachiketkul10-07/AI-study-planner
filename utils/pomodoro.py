"""
pomodoro.py — Pomodoro Timer component for AI Study Planner
Renders a self-contained HTML/CSS/JS timer via st.components.v1.html()
"""

import streamlit.components.v1 as components


def render_pomodoro_timer():
    """Render an interactive Pomodoro timer with SVG ring, modes, and audio."""

    timer_html = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: transparent;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    min-height: 100%;
    color: #e0e0e0;
  }

  .pomodoro-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 20px;
    padding: 28px 24px 20px;
    width: 100%;
    max-width: 460px;
    margin: 0 auto;
  }

  /* ── Mode Selector ─────────────────────────── */
  .mode-selector {
    display: flex;
    gap: 8px;
    background: rgba(255,255,255,0.04);
    border-radius: 12px;
    padding: 4px;
  }

  .mode-btn {
    padding: 8px 20px;
    border: none;
    border-radius: 10px;
    font-size: 0.88rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.25s ease;
    background: transparent;
    color: #888;
  }

  .mode-btn.active {
    background: linear-gradient(135deg, #6C63FF, #3ECFCF);
    color: #fff;
    box-shadow: 0 4px 18px rgba(108,99,255,0.35);
  }

  .mode-btn:not(.active):hover {
    background: rgba(108,99,255,0.12);
    color: #a29bfe;
  }

  /* ── Timer Ring ────────────────────────────── */
  .ring-wrapper {
    position: relative;
    width: 220px;
    height: 220px;
  }

  .timer-ring {
    width: 100%;
    height: 100%;
    transform: rotate(-90deg);
  }

  .ring-bg {
    fill: none;
    stroke: rgba(108,99,255,0.12);
    stroke-width: 8;
  }

  .ring-progress {
    fill: none;
    stroke: url(#ringGradient);
    stroke-width: 8;
    stroke-linecap: round;
    transition: stroke-dashoffset 0.5s ease;
  }

  .timer-center {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
  }

  .timer-digits {
    font-size: 3.2rem;
    font-weight: 700;
    letter-spacing: 2px;
    background: linear-gradient(135deg, #6C63FF, #3ECFCF);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-variant-numeric: tabular-nums;
  }

  .timer-label {
    font-size: 0.8rem;
    color: #888;
    margin-top: 4px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 1.5px;
  }

  /* ── Controls ──────────────────────────────── */
  .controls {
    display: flex;
    gap: 10px;
  }

  .ctrl-btn {
    padding: 10px 28px;
    border: none;
    border-radius: 10px;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .ctrl-btn.primary {
    background: linear-gradient(135deg, #6C63FF, #3ECFCF);
    color: #fff;
    box-shadow: 0 4px 16px rgba(108,99,255,0.3);
  }

  .ctrl-btn.primary:hover {
    opacity: 0.88;
    transform: translateY(-1px);
  }

  .ctrl-btn.secondary {
    background: rgba(255,255,255,0.06);
    color: #aaa;
    border: 1px solid rgba(255,255,255,0.1);
  }

  .ctrl-btn.secondary:hover {
    background: rgba(255,255,255,0.1);
    color: #e0e0e0;
  }

  /* ── Session Counter ───────────────────────── */
  .session-info {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 0.88rem;
    color: #888;
  }

  .session-count {
    font-weight: 700;
    font-size: 1.1rem;
    color: #6C63FF;
  }

  .session-dots {
    display: flex;
    gap: 4px;
  }

  .session-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: rgba(108,99,255,0.2);
    transition: background 0.3s ease;
  }

  .session-dot.filled {
    background: linear-gradient(135deg, #6C63FF, #3ECFCF);
    box-shadow: 0 0 6px rgba(108,99,255,0.5);
  }

  /* ── Break Banner ──────────────────────────── */
  .break-banner {
    display: none;
    background: rgba(62,207,207,0.1);
    border: 1px solid rgba(62,207,207,0.25);
    border-radius: 10px;
    padding: 10px 20px;
    font-size: 0.88rem;
    color: #3ECFCF;
    text-align: center;
    animation: pulse 2s infinite;
  }

  .break-banner.visible { display: block; }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }
</style>
</head>
<body>
<div class="pomodoro-container">

  <!-- Mode Selector -->
  <div class="mode-selector">
    <button class="mode-btn active" id="btn-pomodoro" onclick="setMode('pomodoro')">🍅 Pomodoro</button>
    <button class="mode-btn" id="btn-deepwork" onclick="setMode('deepwork')">🧠 Deep Work</button>
  </div>

  <!-- Timer Ring -->
  <div class="ring-wrapper">
    <svg class="timer-ring" viewBox="0 0 200 200">
      <defs>
        <linearGradient id="ringGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#6C63FF"/>
          <stop offset="100%" stop-color="#3ECFCF"/>
        </linearGradient>
      </defs>
      <circle class="ring-bg" cx="100" cy="100" r="90"/>
      <circle class="ring-progress" id="ring-progress" cx="100" cy="100" r="90"
              stroke-dasharray="565.48" stroke-dashoffset="0"/>
    </svg>
    <div class="timer-center">
      <div class="timer-digits" id="timer-digits">25:00</div>
      <div class="timer-label" id="timer-label">Focus Time</div>
    </div>
  </div>

  <!-- Break Banner -->
  <div class="break-banner" id="break-banner">☕ Break time! Stretch, hydrate, rest your eyes.</div>

  <!-- Controls -->
  <div class="controls">
    <button class="ctrl-btn primary" id="btn-start" onclick="toggleTimer()">▶ Start</button>
    <button class="ctrl-btn secondary" onclick="resetTimer()">↺ Reset</button>
  </div>

  <!-- Session Counter -->
  <div class="session-info">
    <span>Sessions:</span>
    <span class="session-count" id="session-count">0</span>
    <div class="session-dots" id="session-dots"></div>
  </div>

</div>

<script>
  const MODES = {
    pomodoro: { focus: 25, break: 5, label: 'Pomodoro' },
    deepwork: { focus: 50, break: 10, label: 'Deep Work' }
  };

  let currentMode = 'pomodoro';
  let totalSeconds = MODES.pomodoro.focus * 60;
  let remainingSeconds = totalSeconds;
  let isRunning = false;
  let isBreak = false;
  let intervalId = null;
  let sessions = 0;

  const circumference = 2 * Math.PI * 90; // 565.48

  const ring = document.getElementById('ring-progress');
  const digits = document.getElementById('timer-digits');
  const label = document.getElementById('timer-label');
  const btnStart = document.getElementById('btn-start');
  const breakBanner = document.getElementById('break-banner');
  const sessionCount = document.getElementById('session-count');
  const sessionDots = document.getElementById('session-dots');

  ring.style.strokeDasharray = circumference;

  function updateDisplay() {
    const mins = Math.floor(remainingSeconds / 60);
    const secs = remainingSeconds % 60;
    digits.textContent = String(mins).padStart(2, '0') + ':' + String(secs).padStart(2, '0');

    const progress = 1 - (remainingSeconds / totalSeconds);
    ring.style.strokeDashoffset = circumference * (1 - progress);
  }

  function playBeep() {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const frequencies = [523.25, 659.25, 783.99]; // C5, E5, G5
      frequencies.forEach((freq, i) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.frequency.value = freq;
        osc.type = 'sine';
        gain.gain.setValueAtTime(0.15, ctx.currentTime + i * 0.18);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + i * 0.18 + 0.4);
        osc.start(ctx.currentTime + i * 0.18);
        osc.stop(ctx.currentTime + i * 0.18 + 0.4);
      });
    } catch(e) {}
  }

  function setMode(mode) {
    currentMode = mode;
    document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('btn-' + mode).classList.active;
    if (mode === 'pomodoro') document.getElementById('btn-pomodoro').classList.add('active');
    else document.getElementById('btn-deepwork').classList.add('active');

    clearInterval(intervalId);
    isRunning = false;
    isBreak = false;
    totalSeconds = MODES[mode].focus * 60;
    remainingSeconds = totalSeconds;
    label.textContent = 'Focus Time';
    btnStart.textContent = '▶ Start';
    breakBanner.classList.remove('visible');
    updateDisplay();
  }

  function toggleTimer() {
    if (isRunning) {
      clearInterval(intervalId);
      isRunning = false;
      btnStart.textContent = '▶ Resume';
    } else {
      isRunning = true;
      btnStart.textContent = '⏸ Pause';
      intervalId = setInterval(() => {
        remainingSeconds--;
        if (remainingSeconds <= 0) {
          clearInterval(intervalId);
          isRunning = false;
          playBeep();

          if (!isBreak) {
            // Focus done → start break
            sessions++;
            sessionCount.textContent = sessions;
            updateDots();
            isBreak = true;
            totalSeconds = MODES[currentMode].break * 60;
            remainingSeconds = totalSeconds;
            label.textContent = 'Break Time';
            breakBanner.classList.add('visible');
            btnStart.textContent = '▶ Start Break';
          } else {
            // Break done → ready for next focus
            isBreak = false;
            totalSeconds = MODES[currentMode].focus * 60;
            remainingSeconds = totalSeconds;
            label.textContent = 'Focus Time';
            breakBanner.classList.remove('visible');
            btnStart.textContent = '▶ Start';
          }
        }
        updateDisplay();
      }, 1000);
    }
  }

  function resetTimer() {
    clearInterval(intervalId);
    isRunning = false;
    isBreak = false;
    totalSeconds = MODES[currentMode].focus * 60;
    remainingSeconds = totalSeconds;
    label.textContent = 'Focus Time';
    btnStart.textContent = '▶ Start';
    breakBanner.classList.remove('visible');
    updateDisplay();
  }

  function updateDots() {
    sessionDots.innerHTML = '';
    const count = Math.min(sessions, 12);
    for (let i = 0; i < count; i++) {
      const dot = document.createElement('div');
      dot.className = 'session-dot filled';
      sessionDots.appendChild(dot);
    }
  }

  updateDisplay();
</script>
</body>
</html>
"""

    components.html(timer_html, height=480, scrolling=False)
