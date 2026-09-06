const REMOTE_DATA = "https://raw.githubusercontent.com/DnSiii/CryptoAI-Lab/paper-results/dashboard/dashboard_data.json";
const COLORS = { v14: "#76a7ff", v15: "#b78cff", v16: "#54d7e6", v99: "#a6ff4d" };
const state = {
  data: null,
  selectedPaperEngine: "v99",
  selectedBacktest: new Set(["v14", "v15", "v16", "v99"]),
  presetDays: 365,
};

const brl = (value, digits = 2) => Number(value || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL", minimumFractionDigits: digits, maximumFractionDigits: digits });
const pct = (value, digits = 2) => `${Number(value) >= 0 ? "+" : ""}${Number(value || 0).toFixed(digits).replace(".", ",")}%`;
const date = (value) => value ? new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric", timeZone: "UTC" }).format(new Date(value)) : "—";
const dateTime = (value) => value ? new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit", timeZone: "UTC" }).format(new Date(value)) : "—";
const cls = (value) => Number(value) >= 0 ? "positive" : "negative";

async function fetchJson(url) {
  const response = await fetch(`${url}${url.includes("?") ? "&" : "?"}t=${Date.now()}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json();
}

async function loadData() {
  try { return await fetchJson(REMOTE_DATA); }
  catch (remoteError) {
    console.warn("Paper-results dashboard unavailable; using local snapshot", remoteError);
    return fetchJson("dashboard_data.json");
  }
}

function setView(id) {
  document.querySelectorAll(".view").forEach((view) => view.classList.toggle("active", view.id === id));
  document.querySelectorAll(".nav-btn").forEach((button) => button.classList.toggle("active", button.dataset.view === id));
  requestAnimationFrame(() => {
    if (id === "overview" || id === "paper") drawPaperChart();
    if (id === "backtest") renderBacktest();
  });
}

function bindNavigation() {
  document.querySelectorAll(".nav-btn").forEach((button) => button.addEventListener("click", () => setView(button.dataset.view)));
}

function engineCard(engine) {
  const badge = engine.track === "v99" ? "FROZEN" : engine.role;
  return `<article class="engine-card ${engine.track} ${engine.track === state.selectedPaperEngine ? "selected" : ""}" data-paper-engine="${engine.track}">
    <div class="engine-head">
      <div class="engine-name"><small>${engine.label} · ${engine.role}</small><strong>${engine.name}</strong></div>
      <span class="tag">${badge}</span>
    </div>
    <div class="engine-roi ${cls(engine.roiPct)}">${pct(engine.roiPct)}</div>
    <div class="engine-capital">${brl(engine.currentCapitalBrl)} de ${brl(engine.baseCapitalBrl)}</div>
    <div class="engine-meta">
      <div class="mini-stat"><span>Forward</span><strong>${engine.newForwardHours || 0}h</strong></div>
      <div class="mini-stat"><span>Exposição</span><strong>${Number(engine.grossExposurePct || 0).toFixed(1).replace(".", ",")}%</strong></div>
    </div>
  </article>`;
}

function paperEngines() {
  return Object.values(state.data.paper?.engines || {});
}

function renderOverview() {
  const engines = paperEngines();
  document.querySelector("#paper-engine-cards").innerHTML = engines.map(engineCard).join("");
  document.querySelectorAll("[data-paper-engine]").forEach((card) => card.addEventListener("click", () => {
    state.selectedPaperEngine = card.dataset.paperEngine;
    renderOverview();
    renderPaperDetail();
  }));
  const v99 = state.data.paper?.engines?.v99;
  const heroStatus = document.querySelector("#hero-status-value");
  if (v99) heroStatus.textContent = v99.forwardValidation === "PENDING_INDEPENDENT_DATA" ? "Forward iniciado" : (v99.status || "Tracking");
  document.querySelector("#hero-status-note").textContent = v99?.paperStart ? `Boundary independente: ${dateTime(v99.paperStart)} UTC` : "Aguardando primeiro boundary independente";
  renderPaperDetail();
  drawPaperChart();
}

function renderPaperDetail() {
  const engine = state.data.paper?.engines?.[state.selectedPaperEngine];
  const holder = document.querySelector("#paper-detail");
  if (!engine) { holder.innerHTML = `<div class="empty">Sem dados de paper.</div>`; return; }
  const positions = engine.positions || [];
  holder.innerHTML = `
    <div class="panel-head"><div><p class="eyebrow">${engine.label} · ${engine.role}</p><h3>${engine.name}</h3></div><small>${dateTime(engine.latest)} UTC</small></div>
    <div class="detail-stack">
      ${positions.length ? positions.map((p) => `<div class="position-row"><strong>${p.symbol.replace("USDT", "/USDT")}</strong><span class="direction ${p.direction}">${p.direction === "buy" ? "COMPRA" : "VENDA"}</span><span>${pct(p.weightPct, 1)}</span></div>`).join("") : `<div class="empty" style="min-height:120px">Sem posição simulada aberta agora.</div>`}
    </div>
    ${engine.track === "v99" ? `<div class="note"><strong>V99 Alpha:</strong> peso atual ${Number(engine.satelliteWeightPct || 0).toFixed(2).replace(".", ",")}% · alvo ${Number(engine.satelliteTargetPct || 0).toFixed(2).replace(".", ",")}% · consenso ${Number(engine.consensusPct || 0).toFixed(0)}%. O V16 permanece como núcleo.</div>` : ""}`;
}

function paperChartSeries() {
  return paperEngines().filter((engine) => engine.curve?.length > 1).map((engine) => ({
    key: engine.track,
    label: engine.label,
    color: COLORS[engine.track],
    points: engine.curve.map((p) => ({ time: new Date(p.time).getTime(), value: Number(p.capital) })),
  }));
}

function drawLineChart(canvas, series, options = {}) {
  if (!canvas || !series.length) return;
  const rect = canvas.getBoundingClientRect();
  if (!rect.width || !rect.height) return;
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.round(rect.width * dpr); canvas.height = Math.round(rect.height * dpr);
  const ctx = canvas.getContext("2d"); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const width = rect.width, height = rect.height;
  const pad = { left: 44, right: 14, top: 18, bottom: 28 };
  const all = series.flatMap((s) => s.points);
  if (!all.length) return;
  const minTime = Math.min(...all.map((p) => p.time));
  const maxTime = Math.max(...all.map((p) => p.time));
  let minValue = Math.min(...all.map((p) => p.value));
  let maxValue = Math.max(...all.map((p) => p.value));
  const spread = Math.max(maxValue - minValue, Math.max(Math.abs(maxValue), 1) * .02);
  minValue -= spread * .08; maxValue += spread * .08;
  const x = (t) => pad.left + ((t - minTime) / Math.max(maxTime - minTime, 1)) * (width - pad.left - pad.right);
  const y = (v) => pad.top + ((maxValue - v) / Math.max(maxValue - minValue, 1e-12)) * (height - pad.top - pad.bottom);
  ctx.clearRect(0, 0, width, height);
  ctx.font = "9px Inter, system-ui"; ctx.fillStyle = "#667085"; ctx.textAlign = "right";
  for (let i = 0; i <= 4; i++) {
    const yy = pad.top + (height - pad.top - pad.bottom) * i / 4;
    const value = maxValue - (maxValue - minValue) * i / 4;
    ctx.strokeStyle = "rgba(255,255,255,.055)"; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(pad.left, yy); ctx.lineTo(width - pad.right, yy); ctx.stroke();
    ctx.fillText(options.money ? `R$${Math.round(value).toLocaleString("pt-BR")}` : `${value.toFixed(0)}%`, pad.left - 7, yy + 3);
  }
  series.forEach((s) => {
    if (s.points.length < 2) return;
    ctx.strokeStyle = s.color; ctx.lineWidth = s.key === "v99" ? 2.4 : 1.7; ctx.globalAlpha = s.key === "v99" ? 1 : .72;
    ctx.beginPath(); s.points.forEach((p, i) => { const xx = x(p.time), yy = y(p.value); i ? ctx.lineTo(xx, yy) : ctx.moveTo(xx, yy); }); ctx.stroke();
    ctx.globalAlpha = 1;
  });
  ctx.fillStyle = "#667085"; ctx.textAlign = "left"; ctx.fillText(date(minTime), pad.left, height - 7); ctx.textAlign = "right"; ctx.fillText(date(maxTime), width - pad.right, height - 7);
}

function renderLegend(id, series) {
  const node = document.querySelector(id); if (!node) return;
  node.innerHTML = series.map((s) => `<span class="legend-item"><i style="background:${s.color}"></i>${s.label}</span>`).join("");
}

function drawPaperChart() {
  const series = paperChartSeries();
  renderLegend("#paper-legend", series);
  drawLineChart(document.querySelector("#paper-chart"), series, { money: true });
}

function rawBacktestEngine(key) { return state.data.backtest?.engines?.[key]; }

function periodBounds() {
  const engines = [...state.selectedBacktest].map(rawBacktestEngine).filter(Boolean);
  const all = engines.flatMap((e) => e.curve || []);
  if (!all.length) return { start: null, end: null };
  const end = Math.max(...all.map((p) => new Date(p.time).getTime()));
  if (state.presetDays === "all") return { start: Math.min(...all.map((p) => new Date(p.time).getTime())), end };
  if (state.presetDays === "custom") {
    const from = document.querySelector("#bt-start")?.value;
    const to = document.querySelector("#bt-end")?.value;
    return { start: from ? new Date(`${from}T00:00:00Z`).getTime() : Math.min(...all.map((p) => new Date(p.time).getTime())), end: to ? new Date(`${to}T23:59:59Z`).getTime() : end };
  }
  return { start: end - Number(state.presetDays) * 86400000, end };
}

function sliceCurve(engine, bounds) {
  const points = (engine.curve || []).map((p) => ({ time: new Date(p.time).getTime(), equity: Number(p.equity) })).filter((p) => p.time >= bounds.start && p.time <= bounds.end);
  if (points.length < 2) return null;
  return points;
}

function btMetrics(points, capital) {
  const first = points[0].equity, last = points[points.length - 1].equity;
  const normalized = points.map((p) => ({ time: p.time, value: p.equity / first }));
  let peak = 1, maxDd = 0, best = -Infinity, worst = Infinity;
  for (let i = 0; i < normalized.length; i++) {
    const v = normalized[i].value; peak = Math.max(peak, v); maxDd = Math.min(maxDd, v / peak - 1);
    if (i > 0) { const r = v / normalized[i - 1].value - 1; best = Math.max(best, r); worst = Math.min(worst, r); }
  }
  return { roiPct: (last / first - 1) * 100, finalCapital: capital * last / first, maxDdPct: maxDd * 100, bestDayPct: Number.isFinite(best) ? best * 100 : 0, worstDayPct: Number.isFinite(worst) ? worst * 100 : 0, normalized };
}

function renderBacktest() {
  if (!state.data?.backtest) return;
  const capital = Math.max(1, Number(document.querySelector("#bt-capital")?.value || 10000));
  const bounds = periodBounds();
  const rows = [];
  const chartSeries = [];
  [...state.selectedBacktest].forEach((key) => {
    const engine = rawBacktestEngine(key); if (!engine) return;
    const points = sliceCurve(engine, bounds); if (!points) return;
    const m = btMetrics(points, capital); rows.push({ key, engine, m });
    chartSeries.push({ key, label: engine.label, color: COLORS[key], points: m.normalized.map((p) => ({ time: p.time, value: (p.value - 1) * 100 })) });
  });
  document.querySelector("#backtest-kpis").innerHTML = rows.map(({ key, engine, m }) => `<article class="kpi-card">
    <header><strong>${engine.label} · ${engine.name}</strong><span>${date(bounds.start)} → ${date(bounds.end)}</span></header>
    <div class="kpi-value ${cls(m.roiPct)}">${pct(m.roiPct)}</div>
    <div class="kpi-grid"><div><span>Capital final</span><strong>${brl(m.finalCapital)}</strong></div><div><span>Max DD</span><strong class="negative">${pct(m.maxDdPct)}</strong></div><div><span>Melhor dia</span><strong class="positive">${pct(m.bestDayPct)}</strong></div><div><span>Pior dia</span><strong class="negative">${pct(m.worstDayPct)}</strong></div></div>
  </article>`).join("") || `<div class="error-box">Não há histórico suficiente para esta combinação de período e engines.</div>`;
  renderLegend("#backtest-legend", chartSeries);
  drawLineChart(document.querySelector("#backtest-chart"), chartSeries, { money: false });
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

function renderArchitecture() {
  const v99 = state.data.v99 || {};
  const paper = state.data.paper?.engines?.v99 || {};
  document.querySelector("#architecture-live").innerHTML = `<div class="architecture-flow"><div class="flow-node">V16 CORE<br><strong>${(100 - Number(paper.satelliteWeightPct || 0)).toFixed(1).replace(".", ",")}%</strong></div><span class="flow-arrow">+</span><div class="flow-node">V99 ALPHA<br><strong class="accent">${Number(paper.satelliteWeightPct || 0).toFixed(1).replace(".", ",")}%</strong></div><span class="flow-arrow">→</span><div class="flow-node">V99 FROZEN</div></div><div class="note">${v99.disclosure || "Forward paper independente. Histórico não conta como lucro paper."}</div>`;
}

function renderRuntime() {
  const generated = state.data.generatedAt;
  document.querySelector("#runtime-text").textContent = generated ? `Dados ${dateTime(generated)} UTC` : "Snapshot local";
  document.querySelector("#footer-generated").textContent = generated ? `Atualizado ${dateTime(generated)} UTC` : "Sem heartbeat";
}

function renderAll() {
  renderRuntime(); renderOverview(); renderArchitecture(); bindBacktest(); renderBacktest();
  window.addEventListener("resize", debounce(() => { drawPaperChart(); if (document.querySelector("#backtest").classList.contains("active")) renderBacktest(); }, 120));
}

function debounce(fn, delay) { let id; return (...args) => { clearTimeout(id); id = setTimeout(() => fn(...args), delay); }; }

async function init() {
  bindNavigation();
  try {
    state.data = await loadData();
    if (!state.data?.paper?.engines || !state.data?.backtest?.engines) throw new Error("Snapshot antigo: aguardando publicação do dashboard v2");
    document.querySelector("#loading").remove();
    renderAll();
  } catch (error) {
    document.querySelector("#loading").innerHTML = `<div class="error-box"><strong>Dashboard v2 aguardando o primeiro snapshot.</strong><br><br>${error.message}</div>`;
    console.error(error);
  }
}

init();
