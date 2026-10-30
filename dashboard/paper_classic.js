/* Classic CryptoAI Paper view. Uses the same official paper snapshot already
   loaded by app_v2.js and lazily reads published ledgers for Operações simples. */
const PC_LEDGER_BASE="https://raw.githubusercontent.com/DnSiii/CryptoAI-Lab/paper-results/reports/";
const pcLedgerCache=new Map();
let pcSelectedEngine="v13";

const pcNum=v=>Number(v||0);
const pcPct=(v,d=2)=>`${pcNum(v)>=0?"+":""}${pcNum(v).toFixed(d).replace(".",",")}%`;
const pcBrl=(v,d=2)=>pcNum(v).toLocaleString("pt-BR",{style:"currency",currency:"BRL",minimumFractionDigits:d,maximumFractionDigits:d});
const pcTime=v=>v?new Intl.DateTimeFormat("pt-BR",{day:"2-digit",month:"2-digit",hour:"2-digit",minute:"2-digit",timeZone:DASHBOARD_TIMEZONE}).format(new Date(v)):"—";
const pcDate=v=>v?new Intl.DateTimeFormat("pt-BR",{day:"2-digit",month:"2-digit",year:"numeric",timeZone:DASHBOARD_TIMEZONE}).format(new Date(v)):"—";
const pcEsc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
const pcTone=v=>pcNum(v)>0?"pc-positive":pcNum(v)<0?"pc-negative":"pc-neutral";

function pcPaperEngines(){
  try{return ENGINE_ORDER.map(k=>state?.data?.paper?.engines?.[k]).filter(Boolean)}catch(_e){return[]}
}
function pcRawCurve(e){
  return (e?.curve||[]).map(p=>({time:new Date(p.time).getTime(),capital:pcNum(p.capital)})).filter(p=>Number.isFinite(p.time)&&Number.isFinite(p.capital)).sort((a,b)=>a.time-b.time);
}
function pcReturnFrom(e,targetMs){
  const curve=pcRawCurve(e); if(curve.length<2)return 0;
  const last=curve[curve.length-1]; let base=curve[0];
  for(const p of curve){if(p.time<=targetMs)base=p;else break}
  return base.capital?((last.capital/base.capital)-1)*100:0;
}
function pcStats(e){
  const curve=pcRawCurve(e); if(!curve.length)return{hour:0,day24:0,today:0,total:pcNum(e?.roiPct),capital:pcNum(e?.currentCapitalBrl),latest:0};
  const latest=curve[curve.length-1].time,startToday=localDayStartMs(latest);
  return{hour:pcReturnFrom(e,latest-3600000),day24:pcReturnFrom(e,latest-86400000),today:pcReturnFrom(e,startToday-1),total:pcNum(e?.roiPct),capital:pcNum(e?.currentCapitalBrl||curve.at(-1).capital),latest};
}
function pcLeader(metric){
  const rows=pcPaperEngines().map(e=>({e,s:pcStats(e)}));
  return rows.sort((a,b)=>b.s[metric]-a.s[metric])[0]||null;
}
function pcSummary(){
  const n=document.querySelector("#pc-summary"); if(!n)return;
  const cards=[
    ["hour","Melhor · última hora","Mudança desde a hora anterior"],
    ["day24","Melhor · últimas 24h","Janela móvel de 24 horas"],
    ["today","Melhor · hoje","Desde 00:00 de São Paulo"],
    ["total","Melhor · total do paper","Somente depois do boundary"]
  ];
  n.innerHTML=cards.map(([m,title,note],i)=>{const x=pcLeader(m);return `<article class="pc-summary-card ${i===0?"featured":""}"><span>${title}</span><strong class="${x?pcTone(x.s[m]):"pc-neutral"}">${x?`${pcEsc(x.e.label)} · ${pcPct(x.s[m])}`:"—"}</strong><small>${note}</small></article>`}).join("");
}
function pcEngineCards(){
  const n=document.querySelector("#pc-engine-cards");if(!n)return;
  n.innerHTML=pcPaperEngines().map(e=>{const s=pcStats(e),open=(e.positions||[]).length;return `<article class="pc-engine ${pcEsc(e.track)} ${pcSelectedEngine===e.track?"active":""}" data-pc-card="${pcEsc(e.track)}"><div class="pc-engine-top"><strong>${pcEsc(e.label)}</strong><span>${e.track==="v99"?"FROZEN":"PAPER"}</span></div><div class="pc-engine-capital">${pcBrl(s.capital)}</div><div class="pc-engine-roi ${pcTone(s.total)}">Total ${pcPct(s.total)}</div><div class="pc-mini-grid"><div class="pc-mini"><span>Última hora</span><strong class="${pcTone(s.hour)}">${pcPct(s.hour)}</strong></div><div class="pc-mini"><span>24 horas</span><strong class="${pcTone(s.day24)}">${pcPct(s.day24)}</strong></div><div class="pc-mini"><span>Hoje</span><strong class="${pcTone(s.today)}">${pcPct(s.today)}</strong></div><div class="pc-mini"><span>Posições</span><strong>${open} · ${pcNum(e.grossExposurePct).toFixed(0)}%</strong></div></div></article>`}).join("");
  n.querySelectorAll("[data-pc-card]").forEach(el=>el.addEventListener("click",()=>{pcSelectedEngine=el.dataset.pcCard;pcEngineCards();pcSyncFilters();pcRenderOperations()}));
}
function pcAnalysis(){
  const n=document.querySelector("#pc-analysis-text");if(!n)return;
  const h=pcLeader("hour"),d=pcLeader("day24"),t=pcLeader("total"),engines=pcPaperEngines();
  if(!h||!d||!t){n.textContent="Aguardando dados suficientes do paper.";return}
  const exposure=[...engines].sort((a,b)=>pcNum(b.grossExposurePct)-pcNum(a.grossExposurePct))[0];
  const positioned=engines.filter(e=>(e.positions||[]).length>0).length;
  n.innerHTML=`Na última hora, <strong>${pcEsc(h.e.label)}</strong> teve o melhor resultado (${pcPct(h.s.hour)}). Nas últimas 24 horas, <strong>${pcEsc(d.e.label)}</strong> lidera com ${pcPct(d.s.day24)}. No total acumulado desde o início de cada paper, <strong>${pcEsc(t.e.label)}</strong> está à frente com ${pcPct(t.s.total)}. Agora, ${positioned} de ${engines.length} engines têm posição simulada aberta; a maior exposição é do ${pcEsc(exposure.label)} (${pcNum(exposure.grossExposurePct).toFixed(1).replace(".",",")}% bruto). <strong>Calendário diário: America/Sao_Paulo. Esses números são do paper forward, não do backtest.</strong>`;
}
function pcHourlyRows(){
  const engines=pcPaperEngines(),latest=Math.max(0,...engines.flatMap(e=>pcRawCurve(e).map(p=>p.time))),cut=latest-24*3600000,maps={},times=new Set;
  engines.forEach(e=>{const c=pcRawCurve(e),m=new Map;for(let i=1;i<c.length;i++){if(c[i].time<cut)continue;const r=c[i-1].capital?((c[i].capital/c[i-1].capital)-1)*100:null;m.set(c[i].time,r);times.add(c[i].time)}maps[e.track]=m});
  return [...times].sort((a,b)=>a-b).map(time=>({time,values:Object.fromEntries(ENGINE_ORDER.map(k=>[k,maps[k]?.get(time)??null]))}));
}
function pcDailyRows(){try{return paperDailyRows()}catch(_e){return[]}}
function pcLegend(selector){
  const n=document.querySelector(selector);if(!n)return;
  n.innerHTML=pcPaperEngines().map(e=>`<span class="legend-item"><i style="background:${COLORS[e.track]}"></i>${pcEsc(e.label)}</span>`).join("");
}
function pcSizeStage(id,count,px=34){
  const stage=document.querySelector(id);if(!stage)return;const scroller=stage.parentElement,avail=Math.max(320,Math.floor(scroller?.clientWidth||800));
  const width=count<=31?avail:Math.max(avail,Math.min(16000,count*px));stage.style.width=`${width}px`;stage.style.minWidth=`${width}px`;stage.style.maxWidth="none";
}
function pcRenderCharts(){
  const hourly=pcHourlyRows(),daily=pcDailyRows();
  const money=paperSeries("money"),perc=paperSeries("pct");
  pcSizeStage("#pc-hourly-stage",hourly.length,46);pcSizeStage("#pc-daily-stage",daily.length,46);
  pcSizeStage("#pc-value-stage",Math.max(1,...money.map(s=>s.points.length)),38);pcSizeStage("#pc-pct-stage",Math.max(1,...perc.map(s=>s.points.length)),38);
  pcLegend("#pc-hourly-legend");pcLegend("#pc-daily-legend");pcLegend("#pc-value-legend");pcLegend("#pc-pct-legend");
  const keys=ENGINE_ORDER.filter(k=>state?.data?.paper?.engines?.[k]);
  drawBars(document.querySelector("#pc-hourly-chart"),hourly,keys);
  drawBars(document.querySelector("#pc-daily-chart"),daily,keys);
  drawLineChart(document.querySelector("#pc-value-chart"),money,{money:true});
  drawLineChart(document.querySelector("#pc-pct-chart"),perc,{includeZero:true});
}
function pcRenderTable(){
  const n=document.querySelector("#pc-daily-table");if(!n)return;const rows=pcDailyRows();
  n.innerHTML=[...rows].reverse().map(r=>{const avail=ENGINE_ORDER.filter(k=>Number.isFinite(r.values[k])),winner=avail.length?[...avail].sort((a,b)=>r.values[b]-r.values[a])[0]:null;return `<tr><td>${pcDate(r.time)}</td>${ENGINE_ORDER.map(k=>`<td class="${Number.isFinite(r.values[k])?pcTone(r.values[k]):"pc-neutral"}">${Number.isFinite(r.values[k])?pcPct(r.values[k]):"—"}</td>`).join("")}<td class="pc-winner">${winner?`${LABELS[winner]} · ${pcPct(r.values[winner])}`:"—"}</td></tr>`}).join("")||`<tr><td colspan="7">Ainda não há dias completos suficientes.</td></tr>`;
}
async function pcLoadLedger(key){
  if(pcLedgerCache.has(key))return pcLedgerCache.get(key);
  try{const r=await fetch(`${PC_LEDGER_BASE}paper_${key}_ledger.json?t=${Date.now()}`,{cache:"no-store"});if(!r.ok)throw new Error(String(r.status));const j=await r.json();pcLedgerCache.set(key,j);return j}catch(e){console.warn("ledger",key,e);pcLedgerCache.set(key,null);return null}
}
function pcAdjustmentHours(root){
  const out=[],seen=new Set();
  function walk(v){if(!v||typeof v!=="object"||seen.has(v))return;seen.add(v);if(v.timestamp&&Array.isArray(v.adjustments)&&v.adjustments.length)out.push(v);if(Array.isArray(v)){v.forEach(walk);return}Object.values(v).forEach(walk)}
  walk(root);return out.sort((a,b)=>new Date(b.timestamp)-new Date(a.timestamp));
}
function pcActionInfo(a){
  const code=String(a?.action_code||"").toLowerCase(),txt=String(a?.action||"").toLowerCase();
  if(code.includes("close")||txt.includes("encer"))return["ENCERROU","close","posição encerrada"];
  if(code.includes("short")&&(code.includes("increase")||code.includes("open")))return["QUEDA","short","ganha se a moeda cair"];
  if(code.includes("reduce_short"))return["DIMINUIU QUEDA","reduce","reduziu uma posição que ganha com a queda"];
  if(code.includes("reduce")||txt.includes("reduz"))return["DIMINUIU","reduce","reduziu uma posição que ganha se subir"];
  return["COMPROU MAIS","buy","ganha se a moeda subir"];
}
function pcAssetCards(ledger,e){
  const assets=ledger?.assets||{};const entries=Object.entries(assets).filter(([,a])=>a&&(a.status==="open"||Math.abs(pcNum(a.current_weight))>1e-9||pcNum(a.position_value_brl)>0));
  if(entries.length)return entries.map(([sym,a])=>{const dir=a.direction||((pcNum(a.current_weight)<0)?"sell":"buy"),inherited=a.inherited_at_paper_start===true;return `<article class="pc-asset"><div class="pc-asset-head"><strong>${pcEsc(sym.replace("USDT","/USDT"))}</strong><span class="pc-dir ${dir==="sell"?"sell":"buy"}">${dir==="sell"?"GANHA SE CAIR":"GANHA SE SUBIR"}</span></div><div class="pc-asset-main">${pcBrl(a.position_value_brl||0)}</div><small>${a.current_price?`Preço atual: ${pcNum(a.current_price).toLocaleString("pt-BR")}`:"Posição simulada atual"}</small>${Number.isFinite(Number(a.net_result_brl))?`<small class="${pcTone(a.net_result_brl)}">Resultado líquido: ${pcBrl(a.net_result_brl)}</small>`:""}${inherited?`<small>Já existia no início do paper; o preço de entrada não é inventado.</small>`:""}</article>`}).join("");
  const pos=e?.positions||[];return pos.map(p=>`<article class="pc-asset"><div class="pc-asset-head"><strong>${pcEsc(p.symbol.replace("USDT","/USDT"))}</strong><span class="pc-dir ${p.direction==="sell"?"sell":"buy"}">${p.direction==="sell"?"GANHA SE CAIR":"GANHA SE SUBIR"}</span></div><div class="pc-asset-main">${pcBrl(p.valueBrl)}</div><small>Exposição: ${pcPct(p.weightPct,1)}</small></article>`).join("")||`<div class="pc-empty">Nenhuma posição simulada aberta neste momento.</div>`;
}
async function pcRenderOperations(){
  const n=document.querySelector("#pc-operations");if(!n)return;const e=state?.data?.paper?.engines?.[pcSelectedEngine];if(!e){n.innerHTML=`<div class="pc-empty">Sem dados para este engine.</div>`;return}
  n.innerHTML=`<div class="pc-empty">Carregando operações oficiais de ${pcEsc(e.label)}…</div>`;
  const ledger=await pcLoadLedger(pcSelectedEngine),hours=pcAdjustmentHours(ledger).slice(0,12);
  const assets=pcAssetCards(ledger,e);
  const ops=hours.flatMap(h=>(h.adjustments||[]).map(a=>({h,a}))).slice(0,18);
  n.innerHTML=`<div class="pc-current-assets">${assets}</div><div class="pc-ops-list">${ops.length?ops.map(({h,a})=>{const[label,tone,goal]=pcActionInfo(a),result=Number.isFinite(Number(a.net_result_brl))?Number(a.net_result_brl):Number(h.net_result_brl);return `<article class="pc-op"><div class="pc-op-top"><div><span class="pc-action ${tone}">${label}</span><h4>${pcEsc(a.symbol?.replace("USDT","/USDT")||"Operação")}</h4><time>${pcTime(h.timestamp)} · São Paulo</time></div><strong class="${pcTone(result)}">${Number.isFinite(result)?pcBrl(result):"—"}</strong></div><div class="pc-op-grid"><div class="pc-op-metric"><span>Valor movimentado</span><strong>${Number.isFinite(Number(a.order_value_brl))?pcBrl(a.order_value_brl):"—"}</strong></div><div class="pc-op-metric"><span>Preço do ajuste</span><strong>${Number.isFinite(Number(a.execution_price))?pcNum(a.execution_price).toLocaleString("pt-BR",{maximumFractionDigits:8}):"—"}</strong></div><div class="pc-op-metric"><span>Antes</span><strong>${Number.isFinite(Number(a.previous_weight))?pcPct(pcNum(a.previous_weight)*100,1):"—"}</strong></div><div class="pc-op-metric"><span>Depois</span><strong>${Number.isFinite(Number(a.new_weight))?pcPct(pcNum(a.new_weight)*100,1):"—"}</strong></div></div><div class="pc-op-note">Objetivo: ${goal}. ${a.result_scope==="whole_asset_hour_not_order_profit"?"O resultado mostrado é da posição inteira dessa moeda naquela hora, não apenas do pequeno ajuste.":""}</div></article>`}).join(""):`<div class="pc-empty">O ledger atual deste engine não publica ajustes detalhados nesse formato. As posições atuais acima continuam vindo do paper oficial; nenhum preço de entrada foi inventado.</div>`}</div>`;
}
function pcSyncFilters(){document.querySelectorAll("[data-pc-engine]").forEach(b=>b.classList.toggle("active",b.dataset.pcEngine===pcSelectedEngine))}
function pcBindFilters(){document.querySelectorAll("[data-pc-engine]").forEach(b=>b.addEventListener("click",()=>{pcSelectedEngine=b.dataset.pcEngine;pcSyncFilters();pcEngineCards();pcRenderOperations()}));pcSyncFilters()}
function renderPaperClassic(){
  if(!state?.data?.paper)return;pcSummary();pcEngineCards();pcAnalysis();pcRenderCharts();pcRenderTable();pcRenderOperations();
  const status=document.querySelector("#pc-live-status"),note=document.querySelector("#pc-live-note");if(status)status.textContent="PAPER ATUALIZADO";if(note)note.textContent=`Snapshot ${pcTime(state.data.generatedAt)} · São Paulo`;
}
function pcApplyPaperBranding(){
  document.title="CryptoAI Paper Dashboard · Backtest CryptoAI";const k=document.querySelector("#page-title"),s=document.querySelector("#page-subtitle"),kick=document.querySelector(".top-kicker"),foot=document.querySelector(".footer span:first-child");
  if(k)k.textContent="CryptoAI Paper Dashboard";if(s)s.textContent="Última hora, últimas 24h, total, histórico por hora/dia e operações simples · America/Sao_Paulo.";if(kick)kick.textContent="CRYPTOAI · PAPER TRADING";if(foot)foot.textContent="CryptoAI Paper Dashboard · PAPER ONLY";
}
function pcActivateFromNav(button){
  if(button.dataset.view==="paper"){setTimeout(()=>{pcApplyPaperBranding();renderPaperClassic()},0)}else if(button.dataset.view==="backtest"){setTimeout(()=>{if(typeof applyBacktestBranding==="function")applyBacktestBranding()},0)}
}
function pcWaitForData(){
  let tries=0;const timer=setInterval(()=>{tries++;try{if(state?.data?.paper){clearInterval(timer);if(document.querySelector("#paper")?.classList.contains("active"))renderPaperClassic()}}catch(_e){}if(tries>200)clearInterval(timer)},100);
}
async function pcRefreshOfficialSnapshot(){
  try{if(typeof loadData!=="function")return;state.data=await loadData();const rt=document.querySelector("#runtime-text"),fg=document.querySelector("#footer-generated");if(rt)rt.textContent=`Snapshot ${pcTime(state.data.generatedAt)} · São Paulo`;if(fg)fg.textContent=`Atualizado ${pcTime(state.data.generatedAt)} · São Paulo`;pcLedgerCache.clear();if(document.querySelector("#paper")?.classList.contains("active"))renderPaperClassic()}catch(e){console.warn("paper refresh",e)}
}
document.addEventListener("DOMContentLoaded",()=>{
  pcBindFilters();document.querySelectorAll(".nav-btn").forEach(b=>b.addEventListener("click",()=>pcActivateFromNav(b)));pcWaitForData();setInterval(pcRefreshOfficialSnapshot,300000);
});
