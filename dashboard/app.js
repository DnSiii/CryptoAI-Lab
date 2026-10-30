const state = { data: null, filter: "recent", selectedId: null };

const pct = (value, digits = 2) => `${value >= 0 ? "+" : ""}${Number(value).toFixed(digits).replace(".", ",")}%`;
const plainPct = (value, digits = 1) => `${Number(value).toFixed(digits).replace(".", ",")}%`;
const money = (value) => Number(value).toLocaleString("pt-BR", { maximumFractionDigits: 6 });
const dateTime = (value) => new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "short", year: "2-digit", hour: "2-digit", minute: "2-digit", timeZone: "UTC" }).format(new Date(value)).replace(".", "");

function horizonCard(period, metric, note, featured = false) {
  return `<article class="metric-card ${featured ? "featured" : ""}">
    <div class="period"><span>${period}</span><span>MEDIANA</span></div>
    <h3 class="${metric.medianPct >= 0 ? "positive-text" : "negative-text"}">${pct(metric.medianPct)}</h3>
    <p>${note}</p>
    <div class="metric-bottom"><span>Maior janela <strong>${pct(metric.maxPct)}</strong></span><span>Positivas <strong>${plainPct(metric.positivePct)}</strong></span></div>
  </article>`;
}

function renderOverview() {
  const c = state.data.candidate;
  document.querySelector("#candidate-name").textContent = c.name;
  document.querySelector("#horizon-cards").innerHTML = [
    horizonCard("1 DIA", c.oneDay, "Resultado típico de uma janela diária."),
    horizonCard("7 DIAS", c.sevenDay, "Semana móvel; não exige sacar ou reiniciar."),
    horizonCard("30 DIAS", c.thirtyDay, "Principal janela para acompanhar crescimento.", true),
    `<article class="metric-card"><div class="period"><span>RISCO</span><span>PIOR QUEDA</span></div><h3 class="negative-text">${pct(c.drawdownPct)}</h3><p>Queda do topo até o fundo no replay.</p><div class="metric-bottom"><span>P10 em 30d <strong>${pct(c.thirtyDay.p10Pct)}</strong></span><span>Recuperação <strong>${c.longestRecoveryDays}d</strong></span></div></article>`,
  ].join("");

  const months = state.data.recentMonths;
  const maxAbs = Math.max(...months.map((m) => Math.abs(m.returnPct)), 1);
  document.querySelector("#monthly-chart").innerHTML = months.map((m) => {
    const height = Math.max(3, Math.abs(m.returnPct) / maxAbs * 74);
    const kind = m.returnPct >= 0 ? "win" : "loss";
    return `<div class="month-column"><div class="month-bar ${kind}" style="height:${height}%;--bar-height:${height * 0.9}px"></div><span class="month-value">${pct(m.returnPct, 1)}</span><span class="month-label">${m.month.slice(5)}</span></div>`;
  }).join("");

  const t = state.data.tstDiagnostic;
  document.querySelector("#reality-list").innerHTML = [
    ["Potencial de ganho", `${pct(t.bestTradePct)}`, "Uma operação capturou um movimento grande — exatamente o comportamento procurado.", "positive-text"],
    ["Dano observado", `${pct(t.worstTradePct)}`, "A maior perda ficou muito abaixo do melhor ganho, mas ainda precisa de controle melhor.", "negative-text"],
    ["Problema atual", `${plainPct(t.winRatePct)}`, `Taxa de acerto no TST isolado; ${t.trades} entradas geraram ruído demais.`, "negative-text"],
    ["Conclusão", `${pct(t.totalPct)}`, t.status, "negative-text"],
  ].map(([title, value, note, cls]) => `<div class="reality-item"><header><strong>${title}</strong><span class="${cls}">${value}</span></header><small>${note}</small></div>`).join("");
}

function renderOperations() {
  let operations = state.data.operations;
  if (state.filter === "recent") operations = operations.filter((o) => o.label === "recent");
  if (state.filter === "wins") operations = operations.filter((o) => o.portfolioReturnPct > 0);
  if (state.filter === "losses") operations = operations.filter((o) => o.portfolioReturnPct <= 0);
  if (state.filter === "highlights") operations = operations.filter((o) => o.label.startsWith("highlight"));
  const list = document.querySelector("#trade-list");
  if (!operations.length) {
    list.innerHTML = `<div class="trade-empty">Nenhuma operação neste filtro.</div>`;
    state.selectedId = null;
    clearChart();
    return;
  }
  if (!operations.some((o) => o.id === state.selectedId)) state.selectedId = operations[0].id;
  list.innerHTML = operations.map((o) => `<button class="trade-item ${o.id === state.selectedId ? "active" : ""}" data-trade-id="${o.id}">
    <div class="trade-main"><strong>${o.symbol.replace("USDT", "/USDT")}</strong><span class="roi ${o.portfolioReturnPct >= 0 ? "positive-text" : "negative-text"}">${pct(o.portfolioReturnPct)}</span></div>
    <div class="trade-meta"><span class="direction ${o.direction}">${o.direction === "long" ? "COMPRA" : "VENDA"}</span><span>${dateTime(o.entry)}</span><span>${o.hours}h</span></div>
  </button>`).join("");
  list.querySelectorAll("[data-trade-id]").forEach((button) => button.addEventListener("click", () => {
    state.selectedId = button.dataset.tradeId;
    renderOperations();
  }));
  renderSelectedTrade();
}

function clearChart() {
  document.querySelector("#chart-empty").style.display = "grid";
  document.querySelector("#trade-details").innerHTML = "";
  const canvas = document.querySelector("#trade-chart");
  canvas.getContext("2d").clearRect(0, 0, canvas.width, canvas.height);
}

function renderSelectedTrade() {
  const trade = state.data.operations.find((o) => o.id === state.selectedId);
  if (!trade) return clearChart();
  document.querySelector("#chart-empty").style.display = "none";
  document.querySelector("#chart-symbol").textContent = trade.symbol;
  const returnNode = document.querySelector("#chart-return");
  returnNode.textContent = pct(trade.portfolioReturnPct);
  returnNode.className = `chart-return ${trade.portfolioReturnPct >= 0 ? "positive-text" : "negative-text"}`;
  document.querySelector("#trade-details").innerHTML = [
    ["Direção", trade.direction === "long" ? "Compra" : "Venda"],
    ["Entrada", money(trade.entryPrice)],
    ["Saída", money(trade.exitPrice)],
    ["Duração", `${trade.hours} horas`],
    ["Peso máximo", plainPct(trade.maxPortfolioWeightPct)],
  ].map(([label, value]) => `<div class="detail"><span>${label}</span><strong>${value}</strong></div>`).join("");
  drawCandles(trade);
}

function drawCandles(trade) {
  const canvas = document.querySelector("#trade-chart");
  const box = canvas.getBoundingClientRect();
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.max(1, Math.round(box.width * dpr));
  canvas.height = Math.max(1, Math.round(box.height * dpr));
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);
  const width = box.width, height = box.height;
  const pad = { top: 28, right: 58, bottom: 28, left: 12 };
  const chartW = width - pad.left - pad.right, chartH = height - pad.top - pad.bottom;
  const candles = trade.candles;
  const low = Math.min(...candles.map((c) => c.low)), high = Math.max(...candles.map((c) => c.high));
  const range = Math.max(high - low, high * 0.002);
  const y = (price) => pad.top + (high - price) / range * chartH;
  const x = (index) => pad.left + (index + .5) / candles.length * chartW;
  ctx.clearRect(0, 0, width, height);
  ctx.font = "9px Inter, system-ui";
  ctx.textAlign = "left";
  for (let i = 0; i <= 4; i++) {
    const yy = pad.top + chartH * i / 4;
    ctx.strokeStyle = "rgba(255,255,255,.055)"; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(pad.left, yy); ctx.lineTo(width - pad.right + 5, yy); ctx.stroke();
    const price = high - range * i / 4;
    ctx.fillStyle = "#758192"; ctx.fillText(price.toFixed(price < 1 ? 4 : 2), width - pad.right + 10, yy + 3);
  }
  const bodyW = Math.max(2, Math.min(8, chartW / candles.length * .62));
  candles.forEach((c, i) => {
    const xx = x(i), up = c.close >= c.open, color = up ? "#24d18f" : "#ff5f72";
    ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(xx, y(c.high)); ctx.lineTo(xx, y(c.low)); ctx.stroke();
    const top = y(Math.max(c.open, c.close)), bottom = y(Math.min(c.open, c.close));
    ctx.fillRect(xx - bodyW / 2, top, bodyW, Math.max(1.5, bottom - top));
  });
  const closestIndex = (timestamp) => {
    const target = new Date(timestamp).getTime();
    return candles.reduce((best, c, index) => Math.abs(new Date(c.time).getTime() - target) < best.distance ? { index, distance: Math.abs(new Date(c.time).getTime() - target) } : best, { index: 0, distance: Infinity }).index;
  };
  drawMarker(ctx, x(closestIndex(trade.entry)), y(trade.entryPrice), "ENTRADA", "#5b8cff", true, width);
  drawMarker(ctx, x(closestIndex(trade.exit)), y(trade.exitPrice), "SAÍDA", trade.portfolioReturnPct >= 0 ? "#24d18f" : "#ff5f72", false, width);
  ctx.fillStyle = "#758192"; ctx.font = "8px Inter, system-ui";
  ctx.fillText(dateTime(candles[0].time), pad.left, height - 8);
  ctx.textAlign = "right"; ctx.fillText(dateTime(candles[candles.length - 1].time), width - pad.right, height - 8);
}

function drawMarker(ctx, x, y, label, color, above, width) {
  ctx.strokeStyle = color; ctx.lineWidth = 1; ctx.setLineDash([3, 3]);
  ctx.beginPath(); ctx.moveTo(x, 18); ctx.lineTo(x, y); ctx.stroke(); ctx.setLineDash([]);
  const tagW = 47, tagX = Math.min(Math.max(x - tagW / 2, 4), width - tagW - 4), tagY = above ? Math.max(3, y - 24) : Math.min(y + 8, 338);
  ctx.fillStyle = color; ctx.beginPath(); ctx.roundRect(tagX, tagY, tagW, 17, 5); ctx.fill();
  ctx.fillStyle = "#07100d"; ctx.font = "800 7px Inter, system-ui"; ctx.textAlign = "center"; ctx.fillText(label, tagX + tagW / 2, tagY + 11.5);
  ctx.beginPath(); ctx.arc(x, y, 4, 0, Math.PI * 2); ctx.fillStyle = color; ctx.fill();
}

function renderValidation() {
  document.querySelector("#validation-rows").innerHTML = state.data.validation.map((row) => `<div class="validation-row" role="row">
    <strong>${row.scenario}</strong><span>${row.median30dPct == null ? "—" : pct(row.median30dPct)}</span><span>${row.positive30dPct == null ? "—" : plainPct(row.positive30dPct)}</span><span class="${row.drawdownPct < 0 ? "negative-text" : ""}">${row.drawdownPct == null ? "—" : pct(row.drawdownPct)}</span><span class="${row.status === "complete" ? "complete-tag" : "pending-tag"}">${row.status === "complete" ? "CONCLUÍDO" : "PENDENTE"}</span>
  </div>`).join("");
  document.querySelector("#disclosures").innerHTML = state.data.disclosures.map((text, index) => `<div class="disclosure"><span>${String(index + 1).padStart(2, "0")}</span>${text}</div>`).join("");
  document.querySelector("#generated-at").textContent = `Atualizado ${dateTime(state.data.generatedAt)} UTC`;
}

function bindNavigation() {
  document.querySelectorAll(".nav-item").forEach((button) => button.addEventListener("click", () => document.querySelector(`#${button.dataset.target}`).scrollIntoView({ behavior: "smooth" })));
  const sections = [...document.querySelectorAll(".section-block")];
  const observer = new IntersectionObserver((entries) => entries.forEach((entry) => {
    if (entry.isIntersecting) {
      document.querySelectorAll(".nav-item").forEach((button) => button.classList.toggle("active", button.dataset.target === entry.target.id));
    }
  }), { rootMargin: "-25% 0px -65%" });
  sections.forEach((section) => observer.observe(section));
  document.querySelectorAll(".filter").forEach((button) => button.addEventListener("click", () => {
    state.filter = button.dataset.filter;
    document.querySelectorAll(".filter").forEach((item) => item.classList.toggle("active", item === button));
    renderOperations();
  }));
}

async function init() {
  try {
    const response = await fetch("dashboard_data.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.data = await response.json();
    renderOverview(); renderOperations(); renderValidation(); bindNavigation();
    let resizeTimer;
    window.addEventListener("resize", () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(renderSelectedTrade, 90); });
  } catch (error) {
    document.querySelector("#horizon-cards").innerHTML = `<article class="metric-card"><h3>Dados indisponíveis</h3><p>Abra o painel pelo servidor local para carregar o snapshot.</p></article>`;
    console.error(error);
  }
}

init();
