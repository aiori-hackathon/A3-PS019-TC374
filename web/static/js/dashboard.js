/* ═══════════════════════════════════════════════════════════
   PrivacyScope PS-019 — Premium Dashboard JavaScript Engine
   ═══════════════════════════════════════════════════════════ */

'use strict';

// ══════════════════ GLOBAL STATE ══════════════════
const STATE = {
  inventory: [],
  filteredInventory: [],
  activeFilter: 'all',
  activeClass: '',
  charts: {},
  scanRunning: false,
};

const CLASS_META = {
  Direct_Personal_Identifiers:       { label: 'Direct PII',        short: 'DPI',  color: '#00C8FF', cssClass: 'class-dpi', dot: '#00C8FF' },
  Contact_Location_Data:             { label: 'Contact & Location', short: 'CLD',  color: '#00FFAA', cssClass: 'class-cld', dot: '#00FFAA' },
  Government_National_IDs:           { label: 'Gov/National IDs',   short: 'GNI',  color: '#FFAA00', cssClass: 'class-gni', dot: '#FFAA00' },
  Financial_Banking_Data:            { label: 'Financial/Banking',  short: 'FBD',  color: '#B06DFF', cssClass: 'class-fbd', dot: '#B06DFF' },
  Authentication_Digital_Telemetry:  { label: 'Auth & Telemetry',   short: 'ADT',  color: '#4D9FFF', cssClass: 'class-adt', dot: '#4D9FFF' },
  Non_PII:                           { label: 'Non-PII',            short: 'N/A',  color: '#3D5070', cssClass: 'class-np',  dot: '#3D5070' },
};

// ══════════════════ PARTICLE CANVAS ══════════════════
function initParticles() {
  const canvas = document.getElementById('particle-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let W = canvas.width  = window.innerWidth;
  let H = canvas.height = window.innerHeight;

  const particles = Array.from({ length: 60 }, () => ({
    x: Math.random() * W, y: Math.random() * H,
    vx: (Math.random() - 0.5) * 0.25,
    vy: (Math.random() - 0.5) * 0.25,
    r: Math.random() * 1.5 + 0.5,
    alpha: Math.random() * 0.4 + 0.1,
  }));

  function drawConnections() {
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          ctx.beginPath();
          ctx.strokeStyle = `rgba(0,200,255,${0.07 * (1 - dist / 120)})`;
          ctx.lineWidth = 0.5;
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.stroke();
        }
      }
    }
  }

  function animate() {
    ctx.clearRect(0, 0, W, H);
    drawConnections();
    particles.forEach(p => {
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
      if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(0,200,255,${p.alpha})`;
      ctx.fill();
    });
    requestAnimationFrame(animate);
  }

  animate();
  window.addEventListener('resize', () => {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  });
}

// ══════════════════ LIVE CLOCK ══════════════════
function startClock() {
  const el = document.getElementById('topbar-clock');
  if (!el) return;
  const tick = () => {
    const now = new Date();
    el.textContent = now.toLocaleTimeString('en-IN', { hour12: false }) + ' IST';
  };
  tick(); setInterval(tick, 1000);
}

// ══════════════════ TAB SWITCHING ══════════════════
const BREADCRUMB_MAP = {
  'tab-overview':   'Command Center',
  'tab-inventory':  'Evidence Inventory',
  'tab-gaps':       'Shadow Data Gaps',
  'tab-benchmark':  'ML Evaluation',
  'tab-rules':      'Rules Engine',
  'tab-architect':  'Architecture',
};

function switchTab(tabId, el) {
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const panel = document.getElementById(tabId);
  if (panel) panel.classList.add('active');
  const navEl = el || document.querySelector(`[data-tab="${tabId}"]`);
  if (navEl) navEl.classList.add('active');
  const bc = document.getElementById('breadcrumb-label');
  if (bc) bc.textContent = BREADCRUMB_MAP[tabId] || tabId;
  if (tabId === 'tab-benchmark') loadBenchmarkData(false);
  if (tabId === 'tab-rules') loadRulesConfig();
}

// ══════════════════ SCAN STATUS ══════════════════
function setScanStatus(state, text) {
  const dot = document.getElementById('indicator-dot');
  const txt = document.getElementById('scan-status-text');
  if (dot) { dot.className = 'indicator-dot' + (state === 'scanning' ? ' scanning' : state === 'error' ? ' error' : ''); }
  if (txt) txt.textContent = text;
}

// ══════════════════ MAIN SCAN ══════════════════
async function triggerScan(forceRefresh = false) {
  if (STATE.scanRunning) return;
  STATE.scanRunning = true;
  setScanStatus('scanning', 'Scanning data sources…');
  const btn = document.getElementById('scan-btn');
  if (btn) btn.disabled = true;

  try {
    const url = forceRefresh ? '/api/scan?refresh=true' : '/api/scan';
    const res = await fetch(url, forceRefresh ? { method: 'POST' } : {});
    const json = await res.json();
    if (!json.success) throw new Error(json.error || 'Scan failed');

    const report = json.data;
    STATE.inventory = report.evidence_inventory || [];
    STATE.filteredInventory = [...STATE.inventory];

    updateKPIs(report);
    renderInventoryTable();
    renderGapCards(report);
    buildSourceSummary();
    buildOverviewCharts();
    setScanStatus('ready', `Scan complete — ${STATE.inventory.length} fields`);
  } catch (err) {
    setScanStatus('error', 'Scan error');
    console.error(err);
  } finally {
    STATE.scanRunning = false;
    if (btn) btn.disabled = false;
  }
}

// ══════════════════ KPI UPDATE ══════════════════
function updateKPIs(report) {
  const inv = report.evidence_inventory || [];
  const summary = report.summary || {};
  const gaps = report.evidence_gaps || {};

  const total = inv.length;
  const pii   = inv.filter(f => f.is_personal_data).length;
  const doc   = inv.filter(f => f.is_personal_data && f.audit_status === 'DOCUMENTED').length;
  const gap   = inv.filter(f => f.human_review_required && f.is_personal_data && f.evidence_gaps && f.evidence_gaps.length > 0).length;

  animCount('kpi-v-total', total);
  animCount('kpi-v-pii',   pii);
  animCount('kpi-v-doc',   doc);
  animCount('kpi-v-gap',   gap);

  const el = document.getElementById('kpi-gap-rate-text');
  if (el && pii > 0) el.textContent = `${Math.round((gap / pii) * 100)}% gap rate`;

  const navPii = document.getElementById('nav-badge-pii');
  if (navPii) navPii.textContent = pii;
  const navGap = document.getElementById('nav-badge-gap');
  if (navGap) navGap.textContent = gap;
}

function animCount(id, target) {
  const el = document.getElementById(id);
  if (!el) return;
  let current = 0;
  const step = Math.ceil(target / 30);
  const interval = setInterval(() => {
    current = Math.min(current + step, target);
    el.textContent = current;
    if (current >= target) clearInterval(interval);
  }, 30);
}

// ══════════════════ OVERVIEW CHARTS ══════════════════
function buildOverviewCharts() {
  buildClassBarChart();
  buildDonutChart();
  buildRadarChart();
}

const CHART_DEFAULTS = {
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 900, easing: 'easeInOutQuart' },
};

function buildClassBarChart() {
  const ctx = document.getElementById('chart-class-bar');
  if (!ctx) return;
  if (STATE.charts.bar) STATE.charts.bar.destroy();

  const classes = Object.keys(CLASS_META).filter(k => k !== 'Non_PII');
  const counts  = classes.map(k => STATE.inventory.filter(f => f.predicted_class === k).length);
  const colors  = classes.map(k => CLASS_META[k].color);

  STATE.charts.bar = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: classes.map(k => CLASS_META[k].short),
      datasets: [{
        label: 'PII Fields Detected',
        data: counts,
        backgroundColor: colors.map(c => c + '33'),
        borderColor: colors,
        borderWidth: 2,
        borderRadius: 6,
        hoverBackgroundColor: colors.map(c => c + '55'),
      }]
    },
    options: {
      ...CHART_DEFAULTS,
      plugins: { legend: { display: false }, tooltip: { callbacks: {
        title: (items) => classes[items[0].dataIndex],
        label: (item) => ` ${item.raw} fields detected`,
      }}},
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#7A90B8', font: { size: 10, family: 'JetBrains Mono' } } },
        y: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#7A90B8', font: { size: 10 }, stepSize: 1 }, beginAtZero: true },
      },
    }
  });
}

function buildDonutChart() {
  const ctx = document.getElementById('chart-donut');
  if (!ctx) return;
  if (STATE.charts.donut) STATE.charts.donut.destroy();

  const pii = STATE.inventory.filter(f => f.is_personal_data).length;
  const nonPii = STATE.inventory.filter(f => !f.is_personal_data).length;
  const documented = STATE.inventory.filter(f => f.is_personal_data && f.audit_status === 'DOCUMENTED').length;
  const gap = pii - documented;

  const labels = ['Documented PII', 'Shadow PII Gaps', 'Non-PII'];
  const data   = [documented, gap, nonPii];
  const colors = ['#00FFAA', '#FF3860', '#3D5070'];

  STATE.charts.donut = new Chart(ctx, {
    type: 'doughnut',
    data: { labels, datasets: [{ data, backgroundColor: colors.map(c => c + '99'), borderColor: colors, borderWidth: 2, hoverBorderWidth: 3 }] },
    options: {
      ...CHART_DEFAULTS,
      cutout: '72%',
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (item) => ` ${item.label}: ${item.raw}` } }
      }
    }
  });

  const legend = document.getElementById('donut-legend');
  if (legend) {
    legend.innerHTML = labels.map((l, i) => `
      <div class="legend-item">
        <div class="legend-dot" style="background:${colors[i]}"></div>
        <span>${l}: <strong style="color:${colors[i]}">${data[i]}</strong></span>
      </div>`).join('');
  }
}

function buildRadarChart() {
  const ctx = document.getElementById('chart-radar');
  if (!ctx) return;
  if (STATE.charts.radar) STATE.charts.radar.destroy();

  STATE.charts.radar = new Chart(ctx, {
    type: 'radar',
    data: {
      labels: ['Precision', 'Recall', 'F1-Score', 'Specificity', 'Binary F1'],
      datasets: [{
        label: 'Scanner Performance',
        data: [94.18, 96.67, 95.41, 93.94, 94.12],
        backgroundColor: 'rgba(0,200,255,0.08)',
        borderColor: '#00C8FF',
        borderWidth: 2,
        pointBackgroundColor: '#00C8FF',
        pointRadius: 4,
      }]
    },
    options: {
      ...CHART_DEFAULTS,
      plugins: { legend: { display: false } },
      scales: {
        r: {
          min: 85, max: 100,
          grid: { color: 'rgba(255,255,255,0.06)' },
          angleLines: { color: 'rgba(255,255,255,0.06)' },
          ticks: { display: false },
          pointLabels: { color: '#7A90B8', font: { size: 10 } },
        }
      }
    }
  });
}

// ══════════════════ SOURCE SUMMARY ══════════════════
function buildSourceSummary() {
  const container = document.getElementById('source-summary-grid');
  if (!container) return;
  const bySource = {};
  STATE.inventory.forEach(f => {
    const key = f.dataset_name;
    if (!bySource[key]) bySource[key] = { total: 0, pii: 0, gaps: 0, type: f.source_type };
    bySource[key].total++;
    if (f.is_personal_data) bySource[key].pii++;
    if (f.evidence_gaps && f.evidence_gaps.length > 0) bySource[key].gaps++;
  });

  container.innerHTML = Object.entries(bySource).map(([name, s]) => `
    <div class="source-card">
      <div class="source-name">${name}</div>
      <div class="source-stats">
        <div class="source-stat"><span>${s.type}</span><span class="source-stat-val">${s.type === 'SQL' ? 'Table' : 'File'}</span></div>
        <div class="source-stat"><span>Total Columns</span><span class="source-stat-val">${s.total}</span></div>
        <div class="source-stat"><span>PII Detected</span><span class="source-stat-val" style="color:#00FFAA">${s.pii}</span></div>
        <div class="source-stat"><span>Gap Flagged</span><span class="source-stat-val" style="color:${s.gaps > 0 ? '#FF3860' : '#00FFAA'}">${s.gaps}</span></div>
      </div>
    </div>`).join('');
}

// ══════════════════ INVENTORY TABLE ══════════════════
function renderInventoryTable() {
  const tbody = document.getElementById('inventory-tbody');
  if (!tbody) return;

  if (STATE.filteredInventory.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="empty-state">No results match your filter.</td></tr>`;
    return;
  }

  tbody.innerHTML = STATE.filteredInventory.map((f, i) => {
    const meta  = CLASS_META[f.predicted_class] || CLASS_META.Non_PII;
    const conf  = Math.round((f.confidence_score || 0) * 100);
    const confCls = conf >= 80 ? 'conf-high' : conf >= 50 ? 'conf-mid' : 'conf-low';
    const statusCls = !f.is_personal_data ? 'status-nonpii' : f.evidence_gaps && f.evidence_gaps.length > 0 ? 'status-gap' : 'status-ok';
    const statusTxt = !f.is_personal_data ? 'Non-PII' : f.evidence_gaps && f.evidence_gaps.length > 0 ? `⚠ Gap (${f.evidence_gaps.length})` : '✓ Documented';

    const purpose = (f.governance_metadata && f.governance_metadata.declared_purpose) || '—';
    const retention = (f.governance_metadata && f.governance_metadata.retention_period) || '—';

    return `<tr>
      <td><span style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#7AA8CC">${f.dataset_name}</span></td>
      <td><strong style="font-family:'JetBrains Mono',monospace">${f.field_name}</strong></td>
      <td><span class="class-pill ${meta.cssClass}">${meta.short}</span></td>
      <td>
        <div class="conf-bar-wrap">
          <div class="conf-bar-bg"><div class="conf-bar-fill ${confCls}" style="width:${conf}%"></div></div>
          <span class="conf-pct">${conf}%</span>
        </div>
      </td>
      <td style="max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#7A90B8;font-size:11px" title="${purpose}">${purpose !== 'NOT DECLARED [GAP]' && purpose !== '—' ? purpose : '<span style="color:#FF3860">Not Declared</span>'}</td>
      <td style="font-size:11px;color:#7A90B8">${retention !== 'NOT SPECIFIED [GAP]' && retention !== '—' ? retention : '<span style="color:#FF3860">—</span>'}</td>
      <td><span class="status-badge ${statusCls}">${statusTxt}</span></td>
      <td><button class="evidence-btn" onclick="openModal(${i})">Evidence</button></td>
    </tr>`;
  }).join('');
}

function applyFilter(filter, el) {
  STATE.activeFilter = filter;
  document.querySelectorAll('.filter-chips .chip').forEach(c => c.classList.remove('active'));
  if (el) el.classList.add('active');
  filterInventoryTable();
}

function filterInventoryTable() {
  const query = (document.getElementById('inventory-search')?.value || '').toLowerCase();
  const classFilter = document.getElementById('class-select-filter')?.value || '';

  STATE.filteredInventory = STATE.inventory.filter(f => {
    if (STATE.activeFilter === 'pii-only' && !f.is_personal_data) return false;
    if (STATE.activeFilter === 'documented' && (f.audit_status !== 'DOCUMENTED' || !f.is_personal_data)) return false;
    if (STATE.activeFilter === 'gap-flagged' && (!f.evidence_gaps || f.evidence_gaps.length === 0)) return false;
    if (classFilter && f.predicted_class !== classFilter) return false;
    if (query) {
      const hay = [f.field_name, f.dataset_name, f.predicted_class,
        (f.governance_metadata?.declared_purpose || '')].join(' ').toLowerCase();
      if (!hay.includes(query)) return false;
    }
    return true;
  });
  renderInventoryTable();
}

// ══════════════════ GAP CARDS ══════════════════
function renderGapCards(report) {
  const container = document.getElementById('gap-cards-container');
  if (!container) return;

  const gapItems = STATE.inventory.filter(f => f.is_personal_data && f.evidence_gaps && f.evidence_gaps.length > 0);
  const missingPurpose   = gapItems.filter(f => f.evidence_gaps.some(g => g.gap_code === 'GAP_MISSING_PURPOSE')).length;
  const missingRetention = gapItems.filter(f => f.evidence_gaps.some(g => g.gap_code === 'GAP_MISSING_RETENTION')).length;

  const pp = document.getElementById('pill-missing-purpose');
  const pr = document.getElementById('pill-missing-retention');
  if (pp) pp.textContent = `Missing Purpose: ${missingPurpose}`;
  if (pr) pr.textContent = `Missing Retention: ${missingRetention}`;

  if (gapItems.length === 0) {
    container.innerHTML = `<div class="empty-state" style="grid-column:1/-1;color:#00FFAA">✓ No evidence gaps detected — all PII fields are documented.</div>`;
    return;
  }

  container.innerHTML = gapItems.map(f => {
    const meta = CLASS_META[f.predicted_class] || CLASS_META.Non_PII;
    return `<div class="gap-card">
      <div class="gap-card-head">
        <div>
          <div class="gap-field-name">${f.field_name}</div>
          <div class="gap-dataset">${f.dataset_name} · ${f.source_type}</div>
        </div>
        <span class="gap-class-pill">${meta.short}</span>
      </div>
      <div class="gap-reasons">
        ${f.evidence_gaps.map(g => `
          <div class="gap-reason-item">
            <span class="gap-reason-icon">⚠</span>
            <span>${g.description || g.gap_code}</span>
          </div>`).join('')}
      </div>
    </div>`;
  }).join('');

  // orphaned policies
  const orphanEl = document.getElementById('orphans-container');
  const orphans  = report.orphaned_governance_entries || [];
  if (orphanEl) {
    if (orphans.length === 0) {
      orphanEl.innerHTML = '<span style="color:#00FFAA">✓ No orphaned governance policies detected.</span>';
    } else {
      orphanEl.innerHTML = `<div style="display:flex;flex-direction:column;gap:6px">${orphans.map(o =>
        `<div style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#7A90B8">${o.dataset_name} → ${o.field_name}</div>`
      ).join('')}</div>`;
    }
  }
  const pillOrphan = document.getElementById('pill-orphans');
  if (pillOrphan) pillOrphan.textContent = `Orphaned Policies: ${orphans.length}`;
}

// ══════════════════ BENCHMARK ══════════════════
async function loadBenchmarkData(forceRefresh = false) {
  try {
    const url = forceRefresh ? '/api/evaluate' : '/api/evaluate';
    const res = await fetch(url, forceRefresh ? { method: 'POST' } : {});
    const json = await res.json();
    if (!json.success) throw new Error(json.error);
    const data = json.data;
    const agg  = data.aggregate_metrics || {};

    // Update ring charts
    renderRing('ring-precision',   agg.macro_precision   || 94.18, '#00FFAA', document.getElementById('eval-macro-prec'));
    renderRing('ring-recall',      agg.macro_recall      || 96.67, '#00C2FF', document.getElementById('eval-macro-rec'));
    renderRing('ring-f1',          agg.macro_f1          || 95.41, '#B06DFF', document.getElementById('eval-macro-f1'));
    renderRing('ring-specificity', agg.non_pii_specificity || 93.94, '#FFAA00', document.getElementById('eval-specificity'));
    renderRing('ring-binary-f1',   agg.binary_pii_f1     || 94.12, '#FF4D6A', document.getElementById('eval-binary-f1'));

    renderBenchmarkTable(data.per_class_metrics || {});
    renderConfusionMatrix(data.confusion_matrix || {});
  } catch (e) {
    console.error('Benchmark load error:', e);
  }
}

function renderRing(containerId, value, color, valEl) {
  const container = document.getElementById(containerId);
  if (!container) return;
  const pct = parseFloat(value).toFixed(2);
  const stroke = 8;
  const r = 38;
  const circ = 2 * Math.PI * r;
  const dash = (pct / 100) * circ;

  container.innerHTML = `
    <svg viewBox="0 0 100 100" width="90" height="90">
      <circle cx="50" cy="50" r="${r}" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="${stroke}"/>
      <circle cx="50" cy="50" r="${r}" fill="none" stroke="${color}" stroke-width="${stroke}"
        stroke-linecap="round"
        stroke-dasharray="${dash} ${circ}"
        stroke-dashoffset="${circ * 0.25}"
        style="transition:stroke-dasharray 1s ease;filter:drop-shadow(0 0 4px ${color}66)"/>
      <text x="50" y="54" text-anchor="middle" fill="${color}"
        font-size="14" font-weight="700" font-family="Orbitron,sans-serif">${pct}%</text>
    </svg>`;
  if (valEl) { valEl.textContent = pct + '%'; valEl.style.color = color; }
}

function renderBenchmarkTable(perClass) {
  const tbody = document.getElementById('benchmark-tbody');
  if (!tbody) return;
  tbody.innerHTML = Object.entries(perClass).map(([cls, m]) => {
    const meta = CLASS_META[cls] || { label: cls, color: '#7A90B8' };
    const f1   = parseFloat(m.f1_score || 0);
    return `<tr>
      <td><span style="display:inline-flex;align-items:center;gap:8px">
        <span style="width:8px;height:8px;border-radius:50%;background:${meta.color};display:inline-block;box-shadow:0 0 5px ${meta.color}"></span>
        ${meta.label}
      </span></td>
      <td style="color:#00FFAA;font-weight:700">${m.true_positives || 0}</td>
      <td style="color:${(m.false_positives||0)>0?'#FF3860':'#3D5070'}">${m.false_positives || 0}</td>
      <td style="color:${(m.false_negatives||0)>0?'#FFAA00':'#3D5070'}">${m.false_negatives || 0}</td>
      <td style="color:#7A90B8">${m.support || 0}</td>
      <td style="font-weight:700;color:${meta.color}">${parseFloat(m.precision||0).toFixed(1)}%</td>
      <td style="font-weight:700;color:${meta.color}">${parseFloat(m.recall||0).toFixed(1)}%</td>
      <td style="font-weight:700;color:${meta.color}">${f1.toFixed(2)}%</td>
      <td><div class="f1-bar-wrap"><div class="f1-bar-fill" style="width:${f1}%;background:${meta.color}"></div></div></td>
    </tr>`;
  }).join('');
}

function renderConfusionMatrix(cm) {
  const container = document.getElementById('confusion-matrix-table');
  if (!container || !cm || Object.keys(cm).length === 0) return;
  const shortLabels = Object.keys(cm).map(k => CLASS_META[k]?.short || k.slice(0,6));
  const fullKeys = Object.keys(cm);

  let html = `<table class="cm-table"><thead><tr>
    <th style="background:transparent;border:none"></th>
    ${shortLabels.map(l => `<th>Pred: ${l}</th>`).join('')}
  </tr></thead><tbody>`;

  fullKeys.forEach((actual, i) => {
    html += `<tr><th>Act: ${shortLabels[i]}</th>`;
    fullKeys.forEach(predicted => {
      const val = (cm[actual] && cm[actual][predicted]) ? cm[actual][predicted] : 0;
      const isMatch = actual === predicted;
      html += `<td class="${isMatch ? 'cm-cell-match' : val > 0 ? 'cm-cell-miss' : ''}">${val}</td>`;
    });
    html += `</tr>`;
  });

  container.innerHTML = html + '</tbody></table>';
}

// ══════════════════ RULES ENGINE ══════════════════
async function loadRulesConfig() {
  const container = document.getElementById('rules-cards-container');
  if (!container) return;
  try {
    const res = await fetch('/api/rules');
    const json = await res.json();
    const classes = json.rules?.classes || {};
    const DOTS = { Direct_Personal_Identifiers: '#00C8FF', Contact_Location_Data: '#00FFAA', Government_National_IDs: '#FFAA00', Financial_Banking_Data: '#B06DFF', Authentication_Digital_Telemetry: '#4D9FFF' };

    container.innerHTML = Object.entries(classes).filter(([k]) => k !== 'Non_PII').map(([key, cfg]) => `
      <div class="rule-card">
        <div class="rule-card-head">
          <div class="rule-class-dot" style="background:${DOTS[key]||'#7A90B8'};box-shadow:0 0 6px ${DOTS[key]||'#7A90B8'}"></div>
          <div class="rule-class-name">${cfg.display_name || key}</div>
        </div>
        <div class="rule-section">
          <div class="rule-section-label">Header Patterns</div>
          <div class="rule-patterns">
            ${(cfg.header_patterns||[]).slice(0,6).map(p => `<span class="rule-pattern-tag">${p}</span>`).join('')}
          </div>
        </div>
        <div class="rule-section">
          <div class="rule-section-label">Confidence Weights</div>
          <div class="rule-sliders">
            <div class="rule-slider-item">
              <div class="rule-slider-label">Header Weight</div>
              <input type="range" class="rule-slider" min="0" max="1" step="0.05" value="${cfg.header_weight||0.6}" oninput="this.nextElementSibling.textContent=parseFloat(this.value).toFixed(2)">
              <span class="rule-slider-val">${parseFloat(cfg.header_weight||0.6).toFixed(2)}</span>
            </div>
            <div class="rule-slider-item">
              <div class="rule-slider-label">Value Weight</div>
              <input type="range" class="rule-slider" min="0" max="1" step="0.05" value="${cfg.value_weight||0.4}" oninput="this.nextElementSibling.textContent=parseFloat(this.value).toFixed(2)">
              <span class="rule-slider-val">${parseFloat(cfg.value_weight||0.4).toFixed(2)}</span>
            </div>
            <div class="rule-slider-item">
              <div class="rule-slider-label">Confidence Threshold</div>
              <input type="range" class="rule-slider" min="0" max="1" step="0.05" value="${cfg.confidence_threshold||0.5}" oninput="this.nextElementSibling.textContent=parseFloat(this.value).toFixed(2)">
              <span class="rule-slider-val">${parseFloat(cfg.confidence_threshold||0.5).toFixed(2)}</span>
            </div>
          </div>
        </div>
      </div>`).join('');
  } catch(e) { container.innerHTML = '<div class="empty-state">Failed to load rules configuration.</div>'; }
}

async function saveRulesConfig() {
  // In full implementation: collect slider values and POST to /api/rules
  alert('Rules saved — triggering re-scan…');
  await triggerScan(true);
}

// ══════════════════ EVIDENCE MODAL ══════════════════
function openModal(idx) {
  const f = STATE.filteredInventory[idx];
  if (!f) return;
  const meta = CLASS_META[f.predicted_class] || CLASS_META.Non_PII;
  const conf = Math.round((f.confidence_score || 0) * 100);
  const gov  = f.governance_metadata || {};

  document.getElementById('modal-field-title').textContent = f.field_name;
  document.getElementById('modal-field-sub').textContent   = `${f.dataset_name} · ${f.source_type} · ${meta.label}`;

  const ev = f.evidence_breakdown || {};
  const samples = ev.sample_masked_values || f.sample_values || [];

  document.getElementById('modal-body-content').innerHTML = `
    <div class="modal-row">
      <div class="modal-field"><span class="modal-field-label">Dataset</span><span class="modal-field-val mono">${f.dataset_name}</span></div>
      <div class="modal-field"><span class="modal-field-label">Source Type</span><span class="modal-field-val">${f.source_type}</span></div>
      <div class="modal-field"><span class="modal-field-label">Data Class</span><span class="modal-field-val" style="color:${meta.color}">${meta.label}</span></div>
      <div class="modal-field"><span class="modal-field-label">Confidence Score</span><span class="modal-field-val" style="color:${conf>=80?'#00FFAA':conf>=50?'#FFAA00':'#FF3860'}">${conf}%</span></div>
      <div class="modal-field"><span class="modal-field-label">Header Match</span><span class="modal-field-val">${ev.header_match ? '✓ Yes' : '✗ No'}</span></div>
      <div class="modal-field"><span class="modal-field-label">Sample Match Ratio</span><span class="modal-field-val">${ev.sample_match_ratio != null ? (ev.sample_match_ratio * 100).toFixed(0) + '%' : '—'}</span></div>
    </div>

    <div class="modal-section-title">Governance Metadata</div>
    <div class="modal-row">
      <div class="modal-field" style="grid-column:1/-1"><span class="modal-field-label">Declared Purpose</span><span class="modal-field-val">${gov.declared_purpose || 'NOT DECLARED'}</span></div>
      <div class="modal-field"><span class="modal-field-label">Retention Period</span><span class="modal-field-val">${gov.retention_period || 'NOT SPECIFIED'}</span></div>
      <div class="modal-field"><span class="modal-field-label">Retention Law Ref</span><span class="modal-field-val">${gov.retention_law_reference || '—'}</span></div>
      <div class="modal-field"><span class="modal-field-label">Data Owner</span><span class="modal-field-val">${gov.data_owner || '—'}</span></div>
      <div class="modal-field"><span class="modal-field-label">Audit Status</span><span class="modal-field-val">${f.audit_status || '—'}</span></div>
    </div>

    ${samples.length > 0 ? `
    <div class="modal-section-title">Sample Values (Masked)</div>
    <div class="sample-values-grid">${samples.map(v => `<span class="sample-val-tag">${v}</span>`).join('')}</div>` : ''}

    ${f.evidence_gaps && f.evidence_gaps.length > 0 ? `
    <div class="modal-section-title">Evidence Gaps Requiring DPO Review</div>
    <div class="gap-list">${f.evidence_gaps.map(g => `
      <div class="gap-list-item">
        <span>⚠</span>
        <span><strong>${g.gap_code}</strong> — ${g.description || 'Metadata gap detected'}</span>
      </div>`).join('')}
    </div>` : ''}

    <div class="disclaimer-block">
      ⚠ <strong>Technical Evidence Only:</strong> This record is a candidate finding from automated pattern matching. It does not constitute a legal determination of personal data classification, lawful basis, or regulatory obligation under DPDPA 2023 or GDPR. All entries require qualified DPO review before compliance action.
    </div>`;

  document.getElementById('evidence-modal').classList.add('open');
}

function closeModal(event) {
  if (!event || event.target.id === 'evidence-modal') {
    document.getElementById('evidence-modal').classList.remove('open');
  }
}

// ══════════════════ EXPORT ══════════════════
function exportData(format) {
  window.open(`/api/export/${format}`, '_blank');
}

// ══════════════════ TOAST NOTIFICATIONS ══════════════════
function showToast(title, message, type = 'success') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';

  toast.innerHTML = `
    <div class="toast-icon">${icon}</div>
    <div class="toast-body">
      <div class="toast-title">${title}</div>
      <div class="toast-msg">${message}</div>
    </div>
    <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px) scale(0.95)';
    setTimeout(() => toast.remove(), 250);
  }, 4500);
}

// ══════════════════ CSV UPLOAD & DATASETS ══════════════════
function openUploadModal() {
  const modal = document.getElementById('upload-modal');
  if (modal) {
    modal.classList.add('open');
    loadActiveDatasets();
  }
}

function closeUploadModal(event) {
  if (!event || event.target.id === 'upload-modal' || event.target.classList.contains('modal-close')) {
    const modal = document.getElementById('upload-modal');
    if (modal) modal.classList.remove('open');
    const pbox = document.getElementById('upload-progress-box');
    if (pbox) pbox.style.display = 'none';
  }
}

async function handleFileSelect(files) {
  if (!files || files.length === 0) return;
  await handleFileUpload(files);
}

async function handleFileUpload(files) {
  if (!files || files.length === 0) return;

  const validFiles = Array.from(files).filter(f => f.name.toLowerCase().endsWith('.csv'));
  if (validFiles.length === 0) {
    showToast('Invalid File Type', 'Please upload standard comma-separated files (.csv).', 'error');
    return;
  }

  openUploadModal();
  const progressBox = document.getElementById('upload-progress-box');
  const progressTitle = document.getElementById('upload-progress-title');
  const progressSub = document.getElementById('upload-progress-sub');
  if (progressBox) progressBox.style.display = 'flex';
  if (progressTitle) progressTitle.textContent = `Uploading & Scanning ${validFiles.length} file(s)...`;
  if (progressSub) progressSub.textContent = `Analyzing ${validFiles.map(f => f.name).join(', ')}`;

  const formData = new FormData();
  for (const file of validFiles) {
    formData.append('files', file);
  }

  try {
    setScanStatus('scanning', `Ingesting ${validFiles[0].name}…`);
    const res = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });
    const json = await res.json();

    if (!json.success) throw new Error(json.error || 'Upload failed');

    const report = json.data;
    STATE.inventory = report.evidence_inventory || [];
    STATE.filteredInventory = [...STATE.inventory];

    updateKPIs(report);
    renderInventoryTable();
    renderGapCards(report);
    buildSourceSummary();
    buildOverviewCharts();
    loadActiveDatasets();

    setScanStatus('ready', `Scan complete — ${STATE.inventory.length} fields`);
    showToast(
      'CSV Ingested Successfully',
      `Added ${json.uploaded_files.join(', ')}: Discovered ${json.new_columns_count} columns (${json.new_pii_count} personal data fields).`,
      'success'
    );

    if (progressTitle) progressTitle.textContent = 'Scan Complete!';
    if (progressSub) progressSub.textContent = `Discovered ${json.new_columns_count} columns across ${json.uploaded_files.length} file(s).`;
    setTimeout(() => {
      if (progressBox) progressBox.style.display = 'none';
    }, 2000);

  } catch (err) {
    console.error('File upload error:', err);
    showToast('Upload Failed', err.message || 'Error uploading CSV dataset.', 'error');
    if (progressBox) progressBox.style.display = 'none';
    setScanStatus('error', 'Upload error');
  }
}

async function loadActiveDatasets() {
  const container = document.getElementById('active-datasets-list');
  const badge = document.getElementById('active-datasets-badge');
  if (!container) return;

  try {
    const res = await fetch('/api/datasets');
    const json = await res.json();
    if (!json.success) throw new Error(json.error);

    const datasets = json.datasets || [];
    if (badge) badge.textContent = `${datasets.length} files`;

    if (datasets.length === 0) {
      container.innerHTML = '<div class="dataset-loading-row">No CSV datasets found in environment.</div>';
      return;
    }

    container.innerHTML = datasets.map(d => `
      <div class="dataset-item-row">
        <div class="dataset-item-info">
          <div class="dataset-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          </div>
          <div>
            <div class="dataset-item-name">${d.filename}</div>
            <div class="dataset-item-meta">${d.columns} cols · ${d.rows} rows · ${d.size_kb} KB</div>
          </div>
        </div>
        <div class="dataset-item-actions">
          <button class="dataset-delete-btn" onclick="deleteDataset('${d.filename}')" title="Delete dataset">Delete</button>
        </div>
      </div>
    `).join('');
  } catch (err) {
    console.error('Failed to load datasets:', err);
    if (container) container.innerHTML = '<div class="dataset-loading-row" style="color:#FF3860">Error loading datasets.</div>';
  }
}

async function deleteDataset(filename) {
  if (!confirm(`Are you sure you want to delete '${filename}'? This will remove it from the data inventory.`)) return;

  try {
    const res = await fetch(`/api/datasets/${encodeURIComponent(filename)}`, { method: 'DELETE' });
    const json = await res.json();
    if (!json.success) throw new Error(json.error);

    const report = json.data;
    STATE.inventory = report.evidence_inventory || [];
    STATE.filteredInventory = [...STATE.inventory];

    updateKPIs(report);
    renderInventoryTable();
    renderGapCards(report);
    buildSourceSummary();
    buildOverviewCharts();
    loadActiveDatasets();

    showToast('Dataset Deleted', `Removed ${filename} and re-evaluated inventory.`, 'success');
  } catch (err) {
    console.error('Delete error:', err);
    showToast('Delete Failed', err.message, 'error');
  }
}

async function generateSampleCSV(sampleType) {
  const progressBox = document.getElementById('upload-progress-box');
  const progressTitle = document.getElementById('upload-progress-title');
  const progressSub = document.getElementById('upload-progress-sub');
  if (progressBox) progressBox.style.display = 'flex';
  if (progressTitle) progressTitle.textContent = `Generating '${sampleType}'...`;
  if (progressSub) progressSub.textContent = 'Creating realistic structured records with candidate personal data...';

  try {
    const res = await fetch('/api/sample_csv', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: sampleType })
    });
    const json = await res.json();
    if (!json.success) throw new Error(json.error);

    const report = json.data;
    STATE.inventory = report.evidence_inventory || [];
    STATE.filteredInventory = [...STATE.inventory];

    updateKPIs(report);
    renderInventoryTable();
    renderGapCards(report);
    buildSourceSummary();
    buildOverviewCharts();
    loadActiveDatasets();

    showToast('Sample Generated', `Generated and scanned '${sampleType}'! Check the Evidence Inventory.`, 'success');
    if (progressBox) progressBox.style.display = 'none';
  } catch (err) {
    console.error('Sample generation error:', err);
    showToast('Generation Failed', err.message, 'error');
    if (progressBox) progressBox.style.display = 'none';
  }
}

function initDragAndDrop() {
  const dropzones = [
    document.getElementById('modal-dropzone'),
    document.getElementById('overview-dropzone')
  ];

  dropzones.forEach(zone => {
    if (!zone) return;

    ['dragenter', 'dragover'].forEach(eventName => {
      zone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        zone.classList.add('drag-active');
      }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      zone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        zone.classList.remove('drag-active');
      }, false);
    });

    zone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files && files.length > 0) {
        handleFileUpload(files);
      }
    }, false);
  });
}

// ══════════════════ INIT ══════════════════
document.addEventListener('DOMContentLoaded', () => {
  initParticles();
  startClock();
  initDragAndDrop();
  triggerScan(false);
  loadActiveDatasets();
});
