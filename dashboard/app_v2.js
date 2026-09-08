const REMOTE_DATA = "https://raw.githubusercontent.com/DnSiii/CryptoAI-Lab/paper-results/dashboard/dashboard_data.json";
const ENGINE_ORDER = ["v13", "v14", "v15", "v16", "v99"];
const COLORS = {
  v13: "#94a3b8",
  v14: "#5f8cff",
  v15: "#a477ff",
  v16: "#36d7e7",
  v99: "#b7ff4a",
};

const state = {
  data: null,
  selectedPaperEngine: "v99",
  selectedBacktest: new Set(ENGINE_ORDER),
  presetDays: 365,
  overviewDays: 365,
  dailyDays: 30,
};

const brl = (value, digits = 2) => Number(value || 0).toLocaleString("pt-BR", {
  style: "currency", currency: "BRL", minimumFractionDigits: digits, maximumFractionDigits: digits,
});
const pct = (value, digits = 2) => `${Number(value || 0) >= 0 ? "+" : ""}${Number(value || 0).toFixed(digits).replace(".", ",")}%`;
const date = (value) => value ? new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric", timeZone: "UTC" }).format(new Date(value)) : "—";
const shortDate = (value) => value ? new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit", timeZone: "UTC" }).format(new Date(value)) : "—";
const dateTime = (value) => value ? new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit", timeZone: "UTC" }).format(new Date(value)) : "—";
const cls = (value) => Number(value || 0) >= 0 ? "positive" : "negative";
const engineKeys = () => ENGINE_ORDER.filter((key) => state.data?.backtest?.engines?.[key] || state.data?.paper?.engines?.[key]);

async function fetchJson(url) {
  const response = await fetch(`${url}${url.includes("?") ? "&" : "?"}t=${Date.now()}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json();
}

async function loadData() {
  try { return await fetchJson(REMOTE_DATA); }
  catch (remoteError) {
    console.warn("Snapshot remoto indisponível; usando fallback local", remoteError);
    return fetchJson("dashboard_data.json");
  }
}

function setView(id) {
  document.querySelectorAll(".view").forEach((view) => view.classList.toggle("active", view.id === id));
  document.querySelectorAll(".nav-btn").forEach((button) => button.classList.toggle("active", button.dataset.view === id));
  requestAnimationFrame(() => {
    if (id === "overview") renderHistoricalOverview();
    if (id === "paper") drawPaperChart();
    if (id === "backtest") renderBacktest();
  });
}

function bindNavigation() {
  document.querySelectorAll(".nav-btn").forEach((button) => button.addEventListener("click", () => setView(button.dataset.view)));
}

function paperEngines() {
  return ENGINE_ORDER.map((key) => state.data?.paper?.engines?.[key]).filter(Boolean);
}

function engineCard(engine) {
  const badge = engine.track === "v99" ? "FROZEN" : (engine.role || "ENGINE");
  return `<article class="engine-card ${engine.track} ${engine.track === state.selectedPaperEngine ? "selected" : ""}" data-paper-engine="${engine.track}">
    <div class="engine-head">
      <div class="engine-name"><small>${engine.label} · ${engine.role || "Engine"}</small><strong>${engine.name}</strong></div>
      <span class="tag">${badge}</span>
    </div>
    <div class="engine-roi ${cls(engine.roiPct)}">${pct(engine.roiPct)}</div>
    <div class="engine-capital">${brl(engine.currentCapitalBrl)} <span>de ${brl(engine.baseCapitalBrl)}</span></div>
    <div class="engine-meta">
      <div><span>Forward</span><strong>${engine.newForwardHours || 0}h</strong></div>
      <div><span>Exposição</span><strong>${Number(engine.grossExposurePct || 0).toFixed(1).replace(".", ",")}%</strong></div>
    </div>
  </article>`;
}

function renderPaperCards() {
  const html = paperEngines().map(engineCard).join("");
  const primary = document.querySelector("#paper-engine-cards");
  const copy = document.querySelector("#paper-engine-cards-copy");
  if (primary) primary.innerHTML = html;
  if (copy) copy.innerHTML = html;
  document.querySelectorAll("[data-paper-engine]").forEach((card) => card.addEventListener("click", () => {
    state.selectedPaperEngine = card.dataset.paperEngine;
    renderPaperCards();
    renderPaperDetail();
  }));
}

function renderPaperDetail() {
  const engine = state.data?.paper?.engines?.[state.selectedPaperEngine];
  const holder = document.querySelector("#paper-detail");
  if (!holder) return;
  if (!engine) {
    holder.innerHTML = `<div class="empty">Sem dados de paper para este engine.</div>`;
    return;
  }
  const positions = engine.positions || [];
  holder.innerHTML = `
    <div class="panel-head"><div><p class="eyebrow">${engine.label} · ${engine.role || "Engine"}</p><h3>${engine.name}</h3></div><small>${dateTime(engine.latest)} UTC</small></div>
    <div class="paper-summary"><div><span>ROI forward</span><strong class="${cls(engine.roiPct)}">${pct(engine.roiPct)}</strong></div><div><span>Capital</span><strong>${brl(engine.currentCapitalBrl)}</strong></div></div>
    <div class="detail-stack">
      ${positions.length ? positions.map((p) => `<div class="position-row"><strong>${p.symbol.replace("USDT", "/USDT")}</strong><span class="direction ${p.direction}">${p.direction === "buy" ? "COMPRA" : "VENDA"}</span><span>${pct(p.weightPct, 1)}</span></div>`).join("") : `<div class="empty compact-empty">Sem posição simulada aberta agora.</div>`}
    </div>
    ${engine.track === "v99" ? `<div class="note"><strong>V99 Alpha:</strong> peso atual ${Number(engine.satelliteWeightPct || 0).toFixed(2).replace(".", ",")}% · alvo ${Number(engine.satelliteTargetPct || 0).toFixed(2).replace(".", ",")}% · consenso ${Number(engine.consensusPct || 0).toFixed(0)}%. O V16 permanece como núcleo.</div>` : ""}`;
}

function paperChartSeries() {
  return paperEngines().filter((engine) => engine.curve?.length > 1).map((engine) => ({
    key: engine.track,
    label: engine.label,
    color: COLORS[engine.track],
    points: engine.curve.map((p) => ({ time: new Date(p.time).getTime(), value: Number(p.capital) })).filter((p) => Number.isFinite(p.time) && Number.isFinite(p.value)),
  }));
}

function renderLegend(selector, series) {
  const node = document.querySelector(selector);
  if (!node) return;
  node.innerHTML = series.map((s) => `<span class="legend-item"><i style="background:${s.color}"></i>${s.label}</span>`).join("");
}

function chartSize(canvas) {
  if (!canvas) return null;
  const rect = canvas.getBoundingClientRect();
  if (!rect.width || !rect.height) return null;
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.round(rect.width * dpr);
  canvas.height = Math.round(rect.height * dpr);
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { ctx, width: rect.width, height: rect.height };
}

function drawLineChart(canvas, series, options = {}) {
  if (!canvas || !series.length) return;
  const size = chartSize(canvas); if (!size) return;
  const { ctx, width, height } = size;
  const pad = { left: 64, right: 18, top: 18, bottom: 30 };
  const all = series.flatMap((s) => s.points).filter((p) => Number.isFinite(p.time) && Number.isFinite(p.value));
  if (!all.length) return;
  const minTime = Math.min(...all.map((p) => p.time));
  const maxTime = Math.max(...all.map((p) => p.time));
  let minValue = Math.min(...all.map((p) => p.value));
  let maxValue = Math.max(...all.map((p) => p.value));
  if (options.includeZero) { minValue = Math.min(minValue, 0); maxValue = Math.max(maxValue, 0); }
  const spread = Math.max(maxValue - minValue, Math.max(Math.abs(maxValue), 1) * .04);
  minValue -= spread * .08; maxValue += spread * .08;
  const x = (t) => pad.left + ((t - minTime) / Math.max(maxTime - minTime, 1)) * (width - pad.left - pad.right);
  const y = (v) => pad.top + ((maxValue - v) / Math.max(maxValue - minValue, 1e-12)) * (height - pad.top - pad.bottom);
  ctx.clearRect(0, 0, width, height);
  ctx.font = "10px Inter, system-ui"; ctx.fillStyle = "#708199"; ctx.textAlign = "right";
  for (let i = 0; i <= 4; i++) {
    const yy = pad.top + (height - pad.top - pad.bottom) * i / 4;
    const value = maxValue - (maxValue - minValue) * i / 4;
    ctx.strokeStyle = "rgba(148,163,184,.10)"; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(pad.left, yy); ctx.lineTo(width - pad.right, yy); ctx.stroke();
    const label = options.money ? `R$ ${Math.round(value).toLocaleString("pt-BR")}` : `${value >= 0 ? "+" : ""}${value.toFixed(Math.abs(value) < 10 ? 1 : 0).replace(".", ",")}%`;
    ctx.fillText(label, pad.left - 9, yy + 3);
  }
  if (options.includeZero && minValue < 0 && maxValue > 0) {
    const zy = y(0); ctx.strokeStyle = "rgba(255,255,255,.28)"; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(pad.left, zy); ctx.lineTo(width - pad.right, zy); ctx.stroke();
  }
  series.forEach((s) => {
    if (s.points.length < 2) return;
    ctx.strokeStyle = s.color; ctx.lineWidth = s.key === "v99" ? 2.6 : 2; ctx.globalAlpha = s.key === "v99" ? 1 : .82;
    ctx.beginPath();
    s.points.forEach((p, i) => { const xx = x(p.time), yy = y(p.value); i ? ctx.lineTo(xx, yy) : ctx.moveTo(xx, yy); });
    ctx.stroke(); ctx.globalAlpha = 1;
  });
  ctx.fillStyle = "#708199"; ctx.textAlign = "left"; ctx.fillText(shortDate(minTime), pad.left, height - 8); ctx.textAlign = "right"; ctx.fillText(shortDate(maxTime), width - pad.right, height - 8);
}

function drawDailyBars(canvas, rows, keys) {
  const size = chartSize(canvas); if (!size || !rows.length || !keys.length) return;
  const { ctx, width, height } = size;
  const pad = { left: 54, right: 16, top: 18, bottom: 32 };
  const values = rows.flatMap((row) => keys.map((key) => row.values[key])).filter(Number.isFinite);
  if (!values.length) return;
  let min = Math.min(0, ...values), max = Math.max(0, ...values);
  const spread = Math.max(max - min, 1);
  min -= spread * .1; max += spread * .1;
  const y = (v) => pad.top + ((max - v) / Math.max(max - min, 1e-9)) * (height - pad.top - pad.bottom);
  const plotW = width - pad.left - pad.right;
  const groupW = plotW / rows.length;
  const barArea = Math.min(groupW * .82, 28);
  const barW = Math.max(.7, barArea / keys.length);
  ctx.clearRect(0, 0, width, height);
  ctx.font = "10px Inter, system-ui"; ctx.textAlign = "right"; ctx.fillStyle = "#708199";
  for (let i = 0; i <= 4; i++) {
    const yy = pad.top + (height - pad.top - pad.bottom) * i / 4;
    const v = max - (max - min) * i / 4;
    ctx.strokeStyle = "rgba(148,163,184,.10)"; ctx.beginPath(); ctx.moveTo(pad.left, yy); ctx.lineTo(width - pad.right, yy); ctx.stroke();
    ctx.fillText(`${v >= 0 ? "+" : ""}${v.toFixed(1).replace(".", ",")}%`, pad.left - 7, yy + 3);
  }
  const zeroY = y(0); ctx.strokeStyle = "rgba(255,255,255,.34)"; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(pad.left, zeroY); ctx.lineTo(width - pad.right, zeroY); ctx.stroke();
  rows.forEach((row, index) => {
    const center = pad.left + groupW * index + groupW / 2;
    const total = barW * keys.length;
    keys.forEach((key, k) => {
      const v = row.values[key]; if (!Number.isFinite(v)) return;
      const xx = center - total / 2 + k * barW;
      const yy = y(v); const top = Math.min(yy, zeroY); const h = Math.max(1, Math.abs(zeroY - yy));
      ctx.fillStyle = COLORS[key]; ctx.globalAlpha = key === "v99" ? .96 : .76; ctx.fillRect(xx, top, Math.max(.6, barW - .45), h); ctx.globalAlpha = 1;
    });
  });
  const tickCount = Math.min(6, rows.length);
  ctx.fillStyle = "#708199"; ctx.textAlign = "center";
  for (let i = 0; i < tickCount; i++) {
    const idx = Math.round(i * (rows.length - 1) / Math.max(tickCount - 1, 1));
    const xx = pad.left + groupW * idx + groupW / 2;
    ctx.fillText(shortDate(rows[idx].time), xx, height - 8);
  }
}

function drawPaperChart() {
  const series = paperChartSeries();
  renderLegend("#paper-legend", series);
  drawLineChart(document.querySelector("#paper-chart"), series, { money: true });
}

function rawBacktestEngine(key) { return state.data?.backtest?.engines?.[key]; }

function fullBacktestEnd() {
  const times = ENGINE_ORDER.flatMap((key) => (rawBacktestEngine(key)?.curve || []).map((p) => new Date(p.time).getTime())).filter(Number.isFinite);
  return times.length ? Math.max(...times) : null;
}

function historicalSeries(days, mode) {
  const end = fullBacktestEnd(); if (!end) return [];
  const start = days === "all" ? -Infinity : end - Number(days) * 86400000;
  return ENGINE_ORDER.map((key) => {
    const engine = rawBacktestEngine(key); if (!engine) return null;
    const points = (engine.curve || []).map((p) => ({ time: new Date(p.time).getTime(), equity: Number(p.equity) })).filter((p) => Number.isFinite(p.time) && Number.isFinite(p.equity) && p.time >= start && p.time <= end);
    if (points.length < 2) return null;
    const base = points[0].equity;
    return {
      key,
      label: engine.label,
      color: COLORS[key],
      points: points.map((p) => ({ time: p.time, value: mode === "money" ? 10000 * p.equity / base : (p.equity / base - 1) * 100 })),
    };
  }).filter(Boolean);
}

function updateOverviewLeader(seriesPct) {
  const leader = seriesPct.map((s) => ({ key: s.key, label: s.label, value: s.points.at(-1)?.value || 0 })).sort((a, b) => b.value - a.value)[0];
  const title = document.querySelector("#overview-leader");
  const note = document.querySelector("#overview-leader-note");
  if (title) title.textContent = leader ? leader.label : "—";
  if (note) note.textContent = leader ? `${pct(leader.value)} no recorte selecionado` : "Sem histórico disponível";
}

function dailyReturns(engine) {
  const curve = (engine?.curve || []).map((p) => ({ time: new Date(p.time).getTime(), equity: Number(p.equity) })).filter((p) => Number.isFinite(p.time) && Number.isFinite(p.equity)).sort((a, b) => a.time - b.time);
  const out = [];
  for (let i = 1; i < curve.length; i++) {
    if (!curve[i - 1].equity) continue;
    out.push({ time: curve[i].time, value: (curve[i].equity / curve[i - 1].equity - 1) * 100 });
  }
  return out;
}

function dailyRows(days) {
  const byEngine = {};
  let end = 0;
  ENGINE_ORDER.forEach((key) => {
    byEngine[key] = dailyReturns(rawBacktestEngine(key));
    byEngine[key].forEach((p) => { end = Math.max(end, p.time); });
  });
  const start = end - Number(days) * 86400000;
  const map = new Map();
  ENGINE_ORDER.forEach((key) => byEngine[key].forEach((p) => {
    if (p.time < start || p.time > end) return;
    const day = new Date(p.time).toISOString().slice(0, 10);
    if (!map.has(day)) map.set(day, { time: p.time, values: {} });
    map.get(day).values[key] = p.value;
    map.get(day).time = Math.max(map.get(day).time, p.time);
  }));
  return [...map.values()].sort((a, b) => a.time - b.time);
}

function renderDailyResults() {
  const rows = dailyRows(state.dailyDays);
  const keys = ENGINE_ORDER.filter((key) => rawBacktestEngine(key));
  const legend = keys.map((key) => ({ key, label: rawBacktestEngine(key)?.label || key.toUpperCase(), color: COLORS[key], points: [] }));
  renderLegend("#daily-legend", legend);
  drawDailyBars(document.querySelector("#daily-result-chart"), rows, keys);
  const body = document.querySelector("#daily-table-body");
  if (!body) return;
  body.innerHTML = [...rows].reverse().map((row) => {
    const available = keys.map((key) => ({ key, value: row.values[key] })).filter((x) => Number.isFinite(x.value));
    const best = available.sort((a, b) => b.value - a.value)[0];
    return `<tr>
      <td><strong>${date(row.time)}</strong></td>
      ${ENGINE_ORDER.map((key) => Number.isFinite(row.values[key]) ? `<td><span class="daily-value ${cls(row.values[key])}">${pct(row.values[key])}</span></td>` : `<td><span class="muted">—</span></td>`).join("")}
      <td>${best ? `<span class="winner"><i style="background:${COLORS[best.key]}"></i>${best.key.toUpperCase()} ${pct(best.value)}</span>` : "—"}</td>
    </tr>`;
  }).join("") || `<tr><td colspan="7" class="empty">Sem resultados diários para o período.</td></tr>`;
}

function renderHistoricalOverview() {
  if (!state.data?.backtest) return;
  const money = historicalSeries(state.overviewDays, "money");
  const perc = historicalSeries(state.overviewDays, "pct");
  renderLegend("#overview-money-legend", money);
  renderLegend("#overview-pct-legend", perc);
  drawLineChart(document.querySelector("#overview-money-chart"), money, { money: true });
  drawLineChart(document.querySelector("#overview-pct-chart"), perc, { includeZero: true });
  updateOverviewLeader(perc);
  renderDailyResults();
}

function periodBounds() {
  const engines = [...state.selectedBacktest].map(rawBacktestEngine).filter(Boolean);
  const all = engines.flatMap((e) => e.curve || []);
  if (!all.length) return { start: null, end: null };
  const end = Math.max(...all.map((p) => new Date(p.time).getTime()));
  if (state.presetDays === "all") return { start: Math.min(...all.map((p) => new Date(p.time).getTime())), end };
  if (state.presetDays === "custom") {
    const from = document.querySelector("#bt-start")?.value;
    const to = document.querySelector("#bt-end")?.value;
    return {
      start: from ? new Date(`${from}T00:00:00Z`).getTime() : Math.min(...all.map((p) => new Date(p.time).getTime())),
      end: to ? new Date(`${to}T23:59:59Z`).getTime() : end,
    };
  }
  return { start: end - Number(state.presetDays) * 86400000, end };
}

function sliceCurve(engine, bounds) {
  const points = (engine.curve || []).map((p) => ({ time: new Date(p.time).getTime(), equity: Number(p.equity) })).filter((p) => p.time >= bounds.start && p.time <= bounds.end);
  return points.length >= 2 ? points : null;
}

function btMetrics(points, capital) {
  const first = points[0].equity, last = points.at(-1).equity;
  const normalized = points.map((p) => ({ time: p.time, value: p.equity / first }));
  let peak = 1, maxDd = 0, best = -Infinity, worst = Infinity;
  for (let i = 0; i < normalized.length; i++) {
    const v = normalized[i].value; peak = Math.max(peak, v); maxDd = Math.min(maxDd, v / peak - 1);
    if (i > 0) { const r = v / normalized[i - 1].value - 1; best = Math.max(best, r); worst = Math.min(worst, r); }
  }
  return {
    roiPct: (last / first - 1) * 100,
    finalCapital: capital * last / first,
    maxDdPct: maxDd * 100,
    bestDayPct: Number.isFinite(best) ? best * 100 : 0,
    worstDayPct: Number.isFinite(worst) ? worst * 100 : 0,
    normalized,
  };
}

function renderBacktest() {
  if (!state.data?.backtest) return;
  const capital = Math.max(1, Number(document.querySelector("#bt-capital")?.value || 10000));
  const bounds = periodBounds(); if (!bounds.start || !bounds.end) return;
  const rows = [], chartSeries = [];
  ENGINE_ORDER.filter((key) => state.selectedBacktest.has(key)).forEach((key) => {
    const engine = rawBacktestEngine(key); if (!engine) return;
    const points = sliceCurve(engine, bounds); if (!points) return;
    const m = btMetrics(points, capital); rows.push({ key, engine, m });
    chartSeries.push({ key, label: engine.label, color: COLORS[key], points: m.normalized.map((p) => ({ time: p.time, value: (p.value - 1) * 100 })) });
  });
  const holder = document.querySelector("#backtest-kpis");
  if (holder) holder.innerHTML = rows.map(({ engine, m }) => `<article class="kpi-card">
    <header><strong>${engine.label} · ${engine.name}</strong><span>${date(bounds.start)} → ${date(bounds.end)}</span></header>
    <div class="kpi-value ${cls(m.roiPct)}">${pct(m.roiPct)}</div>
    <div class="kpi-grid"><div><span>Capital final</span><strong>${brl(m.finalCapital)}</strong></div><div><span>Max DD</span><strong class="negative">${pct(m.maxDdPct)}</strong></div><div><span>Melhor dia</span><strong class="positive">${pct(m.bestDayPct)}</strong></div><div><span>Pior dia</span><strong class="negative">${pct(m.worstDayPct)}</strong></div></div>
  </article>`).join("") || `<div class="error-box">Não há histórico suficiente para esta combinação.</div>`;
  renderLegend("#backtest-legend", chartSeries);
  drawLineChart(document.querySelector("#backtest-chart"), chartSeries, { includeZero: true });
}

function bindBacktest() {
  document.querySelectorAll(".preset").forEach((button) => button.addEventListener("click", () => {
    state.presetDays = button.dataset.days === "all" ? "all" : Number(button.dataset.days);
    document.querySelectorAll(".preset").forEach((b) => b.classList.toggle("active", b === button));
    renderBacktest();
  }));
  document.querySelectorAll(".engine-toggle").forEach((button) => button.addEventListener("click", () => {
    const key = button.dataset.engine;
    if (state.selectedBacktest.has(key) && state.selectedBacktest.size > 1) state.selectedBacktest.delete(key); else state.selectedBacktest.add(key);
    button.classList.toggle("active", state.selectedBacktest.has(key)); renderBacktest();
  }));
  document.querySelector("#bt-capital")?.addEventListener("input", renderBacktest);
  ["#bt-start", "#bt-end"].forEach((selector) => document.querySelector(selector)?.addEventListener("change", () => {
    state.presetDays = "custom"; document.querySelectorAll(".preset").forEach((b) => b.classList.remove("active")); renderBacktest();
  }));
}

function bindRanges() {
  document.querySelectorAll("#overview-range button").forEach((button) => button.addEventListener("click", () => {
    state.overviewDays = button.dataset.days === "all" ? "all" : Number(button.dataset.days);
    document.querySelectorAll("#overview-range button").forEach((b) => b.classList.toggle("active", b === button));
    renderHistoricalOverview();
  }));
  document.querySelectorAll("#daily-range button").forEach((button) => button.addEventListener("click", () => {
    state.dailyDays = Number(button.dataset.days);
    document.querySelectorAll("#daily-range button").forEach((b) => b.classList.toggle("active", b === button));
    renderDailyResults();
  }));
}

function renderArchitecture() {
  const v99 = state.data?.paper?.engines?.v99;
  const node = document.querySelector("#architecture-live");
  if (!node) return;
  if (!v99) { node.innerHTML = `<div class="empty">Aguardando snapshot V99.</div>`; return; }
  node.innerHTML = `<div class="architecture-live-grid">
    <div><span>Peso alpha atual</span><strong>${Number(v99.satelliteWeightPct || 0).toFixed(2).replace(".", ",")}%</strong></div>
    <div><span>Alvo alpha</span><strong>${Number(v99.satelliteTargetPct || 0).toFixed(2).replace(".", ",")}%</strong></div>
    <div><span>Consenso</span><strong>${Number(v99.consensusPct || 0).toFixed(0)}%</strong></div>
    <div><span>Exposição total</span><strong>${Number(v99.grossExposurePct || 0).toFixed(1).replace(".", ",")}%</strong></div>
  </div>`;
}

function updateRuntime() {
  const runtime = document.querySelector("#runtime-text");
  if (runtime) runtime.textContent = `${state.data?.mode || "PAPER_ONLY"} · ${state.data?.realOrders ? "real habilitado" : "real bloqueado"}`;
  const footer = document.querySelector("#footer-generated");
  if (footer) footer.textContent = `Snapshot ${dateTime(state.data?.generatedAt)} UTC`;
}

function renderAll() {
  renderPaperCards();
  renderPaperDetail();
  renderHistoricalOverview();
  drawPaperChart();
  renderBacktest();
  renderArchitecture();
  updateRuntime();
}

function debounce(fn, wait = 120) {
  let timer; return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), wait); };
}

async function init() {
  bindNavigation(); bindBacktest(); bindRanges();
  try {
    state.data = await loadData();
    document.querySelector("#loading")?.classList.add("hidden");
    renderAll();
  } catch (error) {
    console.error(error);
    const loading = document.querySelector("#loading");
    if (loading) loading.innerHTML = `<div class="error-box">Não foi possível carregar o snapshot do dashboard.<br><small>${String(error.message || error)}</small></div>`;
  }
  window.addEventListener("resize", debounce(() => {
    if (!state.data) return;
    const active = document.querySelector(".view.active")?.id;
    if (active === "overview") renderHistoricalOverview();
    if (active === "paper") drawPaperChart();
    if (active === "backtest") renderBacktest();
  }));
}

document.addEventListener("DOMContentLoaded", init);
