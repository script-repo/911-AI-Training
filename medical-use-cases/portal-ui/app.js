'use strict';

/* ─── Navigation ─────────────────────────────────────────────────── */
const views   = document.querySelectorAll('.view');
const navItems = document.querySelectorAll('.nav-item[data-view]');
const pageTitle = document.getElementById('pageTitle');

const viewTitles = {
  dashboard:  'Dashboard',
  patient:    'Patient Monitoring',
  medication: 'Medication Adherence',
  security:   'Security & Safety',
  vision:     'Vision Hub',
  models:     'Model Library',
  settings:   'Settings',
};

function switchView(viewId) {
  views.forEach(v => v.classList.remove('active'));
  navItems.forEach(n => n.classList.remove('active'));
  const target = document.getElementById('view-' + viewId);
  if (target) target.classList.add('active');
  const navTarget = document.querySelector(`.nav-item[data-view="${viewId}"]`);
  if (navTarget) navTarget.classList.add('active');
  if (pageTitle) pageTitle.textContent = viewTitles[viewId] || viewId;
}

navItems.forEach(item => {
  item.addEventListener('click', e => {
    e.preventDefault();
    switchView(item.dataset.view);
  });
});

/* ─── Sidebar toggle ─────────────────────────────────────────────── */
document.getElementById('sidebarToggle').addEventListener('click', () => {
  document.body.classList.toggle('sidebar-collapsed');
});

/* ─── Panel expand / collapse ────────────────────────────────────── */
function togglePanel(panelId) {
  const panel = document.getElementById(panelId);
  if (!panel) return;
  panel.classList.toggle('collapsed');
}

/* ─── Alert acknowledge ──────────────────────────────────────────── */
function ackAlert(btn) {
  const item = btn.closest('.alert-item');
  if (!item) return;
  item.style.transition = 'opacity 0.3s, max-height 0.35s, margin 0.35s, padding 0.35s';
  item.style.opacity = '0';
  item.style.maxHeight = item.offsetHeight + 'px';
  requestAnimationFrame(() => {
    item.style.maxHeight = '0';
    item.style.padding = '0';
    item.style.margin = '0';
    item.style.overflow = 'hidden';
  });
  setTimeout(() => item.remove(), 370);

  // Update alert count badge
  const remaining = document.querySelectorAll('.alert-item').length - 1;
  const badge = document.getElementById('alertBell')?.querySelector('.alert-count');
  if (badge) {
    badge.textContent = remaining > 0 ? remaining : '';
    if (remaining === 0) badge.style.display = 'none';
  }
  showNotice('Alert acknowledged');
}

/* ─── Toast notifications ────────────────────────────────────────── */
let toastTimer = null;
function showNotice(msg) {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.textContent = msg;
  toast.classList.add('show');
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2800);
}

/* ─── Simulated API explorer ─────────────────────────────────────── */
const apiResponses = {
  '/track': JSON.stringify({
    session_id: "ward-cam-01",
    frame_index: 3841,
    tracks: [
      { id: 1, bbox: [142, 88, 210, 290], class: "person", conf: 0.97 },
      { id: 2, bbox: [320, 102, 388, 295], class: "person", conf: 0.94 }
    ],
    latency_ms: 18
  }, null, 2),
  '/identify': JSON.stringify({
    objects: [
      { label: "medication cup",  conf: 0.91, bbox: [155, 210, 195, 240] },
      { label: "hand",            conf: 0.96, bbox: [130, 190, 220, 280] }
    ],
    model: "CLIP-ViT-L/14",
    latency_ms: 31
  }, null, 2),
  '/segment': JSON.stringify({
    masks: [
      { prompt: "medication cup", mask_rle: "...", area_px: 1204, score: 0.88 },
      { prompt: "hand",           mask_rle: "...", area_px: 8750, score: 0.95 }
    ],
    model: "SAM2-large",
    latency_ms: 52
  }, null, 2),
};

function simulateApi() {
  const endpoint = document.getElementById('apiEndpoint')?.value;
  const responseEl = document.getElementById('apiResponse');
  if (!responseEl) return;

  responseEl.innerHTML = '<span style="color:var(--text-muted)">Running...</span>';

  const delay = 300 + Math.random() * 400;
  setTimeout(() => {
    const resp = apiResponses[endpoint] || '{"error":"unknown endpoint"}';
    responseEl.textContent = resp;
    responseEl.style.color = 'var(--green)';
    setTimeout(() => { responseEl.style.color = ''; }, 800);
  }, delay);
}

/* ─── Mini chart (Patient Monitoring throughput) ─────────────────── */
function drawMiniChart() {
  const canvas = document.getElementById('chart-pm');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;

  // Generate plausible throughput data points
  const pts = Array.from({ length: 30 }, (_, i) => {
    const base = 38 + Math.sin(i * 0.4) * 8;
    return base + (Math.random() - 0.5) * 6;
  });

  const min = Math.min(...pts) - 4;
  const max = Math.max(...pts) + 4;
  const scaleY = v => h - ((v - min) / (max - min)) * h;

  ctx.clearRect(0, 0, w, h);

  // Gradient fill
  const grad = ctx.createLinearGradient(0, 0, 0, h);
  grad.addColorStop(0,   'rgba(59,107,199,0.35)');
  grad.addColorStop(1,   'rgba(59,107,199,0.02)');

  ctx.beginPath();
  pts.forEach((v, i) => {
    const x = (i / (pts.length - 1)) * w;
    const y = scaleY(v);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.lineTo(w, h);
  ctx.lineTo(0, h);
  ctx.closePath();
  ctx.fillStyle = grad;
  ctx.fill();

  // Line
  ctx.beginPath();
  pts.forEach((v, i) => {
    const x = (i / (pts.length - 1)) * w;
    const y = scaleY(v);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.strokeStyle = 'rgba(91,143,219,0.9)';
  ctx.lineWidth = 2;
  ctx.lineJoin = 'round';
  ctx.stroke();

  // Dot at latest point
  const lx = w;
  const ly = scaleY(pts[pts.length - 1]);
  ctx.beginPath();
  ctx.arc(lx - 1, ly, 4, 0, Math.PI * 2);
  ctx.fillStyle = '#5b8fdb';
  ctx.fill();
  ctx.strokeStyle = 'rgba(255,255,255,0.3)';
  ctx.lineWidth = 1.5;
  ctx.stroke();
}

drawMiniChart();

/* ─── Live clock in topbar (subtle) ─────────────────────────────── */
function updateClock() {
  const now = new Date();
  const hh = String(now.getHours()).padStart(2, '0');
  const mm = String(now.getMinutes()).padStart(2, '0');
  const ss = String(now.getSeconds()).padStart(2, '0');
  const bell = document.getElementById('alertBell');
  if (bell) bell.title = `${hh}:${mm}:${ss} — 3 active alerts`;
}
updateClock();
setInterval(updateClock, 1000);

/* ─── Simulated live log updates (Patient Monitoring) ────────────── */
const logMessages = [
  ['log-ok',   'Patient #{n} — vitals summary generated'],
  ['log-ok',   'Patient #{n} — deterioration risk: LOW'],
  ['log-warn', 'Patient #{n} — deterioration risk: MEDIUM — notified charge nurse'],
  ['log-ok',   'Patient #{n} — medication schedule confirmed'],
  ['log-ok',   'Patient #{n} — clinical note updated'],
  ['log-ok',   'Patient #{n} — EHR sync successful'],
];

function addLogLine() {
  const log = document.querySelector('.panel-log');
  if (!log) return;
  const [cls, tpl] = logMessages[Math.floor(Math.random() * logMessages.length)];
  const id = 3700 + Math.floor(Math.random() * 200);
  const msg = tpl.replace('{n}', '#' + id);
  const now = new Date();
  const time = [now.getHours(), now.getMinutes(), now.getSeconds()]
    .map(n => String(n).padStart(2, '0')).join(':');
  const badge = cls === 'log-ok' ? '[OK]' : '[WARN]';

  const line = document.createElement('div');
  line.className = 'log-line';
  line.innerHTML = `<span class="log-time">${time}</span><span class="${cls}">${badge}</span>${msg}`;
  log.insertBefore(line, log.firstChild);
  while (log.children.length > 8) log.removeChild(log.lastChild);
}

setInterval(addLogLine, 4500);

/* ─── Pulsing GPU bars simulation ────────────────────────────────── */
function jitterGPU() {
  document.querySelectorAll('.gpu-fill').forEach(fill => {
    const current = parseFloat(fill.style.width);
    const delta = (Math.random() - 0.5) * 4;
    const next = Math.min(98, Math.max(10, current + delta));
    fill.style.width = next.toFixed(1) + '%';
  });
}
setInterval(jitterGPU, 3000);
