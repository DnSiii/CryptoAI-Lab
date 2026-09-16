/* V99 categorical daily chart renderer.
   Keeps the V99 research data untouched and only changes visualization:
   - backtest charts use one equally-spaced category per Sao Paulo calendar day;
   - paper daily/capital/ROI charts use one category per day;
   - the 24h hourly paper chart remains hourly. */
(function () {
  const DATA_URL = 'https://raw.githubusercontent.com/DnSiii/CryptoAI-Lab/paper-results/dashboard/dashboard_data.json';
  const ORDER = ['r98', 'f1', 'f3', 'f7', 'f12'];
  const COLORS = {r98:'#93a4b8', f1:'#5f8cff', f3:'#a477ff', f7:'#b7ff4a', f12:'#35d6e8'};
  const TZ = 'America/Sao_Paulo';
  let payload = null;
  let scheduled = false;

  const $ = (s, r=document) => r.querySelector(s);
  const $$ = (s, r=document) => [...r.querySelectorAll(s)];
  const partsFmt = new Intl.DateTimeFormat('en-US', {year:'numeric',month:'2-digit',day:'2-digit',timeZone:TZ});
  const labelFmt = new Intl.DateTimeFormat('pt-BR', {day:'2-digit',month:'2-digit',timeZone:TZ});

  function dateKey(value) {
    const parts = Object.fromEntries(partsFmt.formatToParts(new Date(value)).filter(p => p.type !== 'literal').map(p => [p.type,p.value]));
    return `${parts.year}-${parts.month}-${parts.day}`;
  }
  function dateLabel(key) {
    const [y,m,d] = key.split('-').map(Number);
    return labelFmt.format(new Date(Date.UTC(y,m-1,d,15,0,0)));
  }
  function sizeCanvas(canvas) {
    if (!canvas) return null;
    const r = canvas.getBoundingClientRect();
    if (!r.width || !r.height) return null;
    const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    canvas.width = Math.round(r.width * dpr);
    canvas.height = Math.round(r.height * dpr);
    const ctx = canvas.getContext('2d');
    ctx.setTransform(dpr,0,0,dpr,0,0);
    return {ctx,w:r.width,h:r.height};
  }
  function yLabel(v, mode) {
    if (mode === 'money') return `R$ ${Math.round(v).toLocaleString('pt-BR')}`;
    return `${v >= 0 ? '+' : ''}${v.toFixed(Math.abs(v)<10?1:0).replace('.',',')}%`;
  }
  function selected(selector, fallback) {
    const active = $$(selector).filter(b => b.classList.contains('active')).map(b => b.dataset.v99BtEngine || b.dataset.v99PaperEngine);
    return active.length ? active : fallback;
  }
  function lastByDay(curve, valueKey) {
    const by = new Map();
    for (const row of curve || []) {
      if (!row?.time || !Number.isFinite(Number(row[valueKey]))) continue;
      const k = dateKey(row.time);
      const t = new Date(row.time).getTime();
      const prev = by.get(k);
      if (!prev || t >= prev.time) by.set(k, {day:k,time:t,value:Number(row[valueKey])});
    }
    return [...by.values()].sort((a,b) => a.day.localeCompare(b.day));
  }
  function filterDaily(points, start, end, days) {
    let out = points;
    if (start) out = out.filter(p => p.day >= start);
    if (end) out = out.filter(p => p.day <= end);
    if (!start && !end && days) out = out.slice(-Number(days));
    return out;
  }
  function categories(series) {
    return [...new Set(series.flatMap(s => s.points.map(p => p.day)))].sort();
  }
  function fitStage(canvas, count, perDay=30) {
    const stage = canvas?.parentElement;
    const scroller = stage?.parentElement;
    if (!stage || !scroller) return;
    const available = Math.max(760, scroller.clientWidth || 760);
    const width = count <= 31 ? available : Math.max(available, Math.min(24000, count * perDay));
    stage.style.width = `${Math.round(width)}px`;
    stage.style.minWidth = `${Math.round(width)}px`;
  }
  function drawCategoricalLine(id, series, mode='pct', includeZero=false) {
    const canvas = $(id);
    if (!canvas || !series.length) return;
    const cats = categories(series);
    if (!cats.length) return;
    fitStage(canvas, cats.length, 28);
    const sz = sizeCanvas(canvas);
    if (!sz) return;
    const {ctx,w,h} = sz;
    const pad={l:70,r:25,t:26,b:42};
    const all=series.flatMap(s=>s.points.map(p=>p.value)).filter(Number.isFinite);
    if(!all.length)return;
    let minV=Math.min(...all),maxV=Math.max(...all);
    if(includeZero){minV=Math.min(minV,0);maxV=Math.max(maxV,0)}
    let spread=maxV-minV;if(spread<1e-9)spread=Math.max(Math.abs(maxV),1);
    minV-=spread*.1;maxV+=spread*.14;
    const x=i=>cats.length===1?(pad.l+w-pad.r)/2:pad.l+(i/(cats.length-1))*(w-pad.l-pad.r);
    const y=v=>pad.t+((maxV-v)/Math.max(maxV-minV,1e-9))*(h-pad.t-pad.b);
    ctx.clearRect(0,0,w,h);ctx.font='10px system-ui';ctx.fillStyle='#667a92';ctx.strokeStyle='rgba(148,163,184,.09)';ctx.lineWidth=1;
    for(let i=0;i<5;i++){const val=minV+(maxV-minV)*(i/4),yy=y(val);ctx.beginPath();ctx.moveTo(pad.l,yy);ctx.lineTo(w-pad.r,yy);ctx.stroke();ctx.fillText(yLabel(val,mode),6,yy+3)}
    const step=Math.max(1,Math.ceil(cats.length/7));
    cats.forEach((day,i)=>{if(i%step!==0&&i!==cats.length-1)return;const xx=x(i);ctx.fillStyle='#667a92';ctx.fillText(dateLabel(day),Math.max(2,xx-16),h-12)});
    const idx=new Map(cats.map((d,i)=>[d,i]));
    series.forEach(s=>{ctx.strokeStyle=s.color;ctx.lineWidth=2;ctx.beginPath();let started=false;for(const p of s.points){const i=idx.get(p.day);if(i==null)continue;const xx=x(i),yy=y(p.value);if(!started){ctx.moveTo(xx,yy);started=true}else ctx.lineTo(xx,yy)}ctx.stroke();if(cats.length<=70){ctx.fillStyle=s.color;for(const p of s.points){const i=idx.get(p.day);if(i==null)continue;ctx.beginPath();ctx.arc(x(i),y(p.value),2.2,0,Math.PI*2);ctx.fill()}}});
  }
  function drawCategoricalBars(id, series) {
    const canvas=$(id);if(!canvas||!series.length)return;
    const cats=categories(series);if(!cats.length)return;
    fitStage(canvas,cats.length,38);
    const sz=sizeCanvas(canvas);if(!sz)return;const{ctx,w,h}=sz,pad={l:65,r:20,t:22,b:46};
    const maps=Object.fromEntries(series.map(s=>[s.key,new Map(s.points.map(p=>[p.day,p.value]))]));
    const vals=series.flatMap(s=>s.points.map(p=>p.value)).filter(Number.isFinite);if(!vals.length)return;
    let minV=Math.min(0,...vals),maxV=Math.max(0,...vals),spread=maxV-minV;if(spread<1e-9)spread=1;minV-=spread*.08;maxV+=spread*.08;
    const y=v=>pad.t+((maxV-v)/(maxV-minV))*(h-pad.t-pad.b),zero=y(0),groupW=(w-pad.l-pad.r)/Math.max(cats.length,1),barW=Math.max(2,Math.min(14,(groupW*.76)/Math.max(series.length,1)));
    ctx.clearRect(0,0,w,h);ctx.font='9px system-ui';ctx.strokeStyle='rgba(148,163,184,.09)';ctx.fillStyle='#667a92';
    for(let i=0;i<5;i++){const val=minV+(maxV-minV)*(i/4),yy=y(val);ctx.beginPath();ctx.moveTo(pad.l,yy);ctx.lineTo(w-pad.r,yy);ctx.stroke();ctx.fillText(yLabel(val,'pct'),5,yy+3)}
    ctx.strokeStyle='rgba(148,163,184,.22)';ctx.beginPath();ctx.moveTo(pad.l,zero);ctx.lineTo(w-pad.r,zero);ctx.stroke();
    const step=Math.max(1,Math.ceil(cats.length/7));
    cats.forEach((day,di)=>{const gx=pad.l+di*groupW+groupW/2;series.forEach((s,si)=>{const v=maps[s.key].get(day);if(!Number.isFinite(v))return;const xx=gx-(series.length*barW)/2+si*barW,yy=y(v);ctx.fillStyle=s.color;ctx.fillRect(xx,Math.min(yy,zero),Math.max(1,barW-1),Math.abs(zero-yy))});if(di%step===0||di===cats.length-1){ctx.fillStyle='#667a92';ctx.fillText(dateLabel(day),Math.max(2,gx-16),h-12)}});
  }

  function backtestDailySeries(keys) {
    const lab=payload?.v99Research;
    const start=$('#v99-bt-start')?.value||'',end=$('#v99-bt-end')?.value||'';
    const preset=$('[data-v99-bt-days].active');
    const days=!start&&!end&&preset?Number(preset.dataset.v99BtDays):null;
    const raw={};
    for(const k of keys) raw[k]=filterDaily(lastByDay(lab?.backtest?.[k]?.curve,'equity'),start,end,days);
    return raw;
  }
  function redrawBacktest() {
    if(!$('#v99-bt-money')||!payload?.v99Research?.backtest)return;
    const keys=selected('[data-v99-bt-engine]',ORDER).filter(k=>payload.v99Research.backtest[k]);
    const raw=backtestDailySeries(keys);const capital=Math.max(1,Number($('#v99-bt-capital')?.value)||10000);
    const money=[],roi=[],daily=[],dd=[];
    for(const k of keys){const pts=raw[k]||[];if(!pts.length)continue;const first=pts[0].value;let peak=pts[0].value;money.push({key:k,color:COLORS[k],points:pts.map(p=>({day:p.day,value:capital*p.value/first}))});roi.push({key:k,color:COLORS[k],points:pts.map(p=>({day:p.day,value:(p.value/first-1)*100}))});dd.push({key:k,color:COLORS[k],points:pts.map(p=>{peak=Math.max(peak,p.value);return{day:p.day,value:(p.value/peak-1)*100}})});const d=[];for(let i=1;i<pts.length;i++)d.push({day:pts[i].day,value:(pts[i].value/pts[i-1].value-1)*100});daily.push({key:k,color:COLORS[k],points:d})}
    drawCategoricalLine('#v99-bt-money',money,'money');drawCategoricalLine('#v99-bt-pct',roi,'pct',true);drawCategoricalBars('#v99-bt-daily',daily);drawCategoricalLine('#v99-bt-dd',dd,'pct',true);
  }

  function paperWindowRaw(curve) {
    const start=$('#v99-paper-start')?.value||'',end=$('#v99-paper-end')?.value||'';
    let rows=(curve||[]).filter(r=>r?.time&&Number.isFinite(Number(r.capital))).map(r=>({time:new Date(r.time).getTime(),day:dateKey(r.time),value:Number(r.capital)})).sort((a,b)=>a.time-b.time);
    if(start)rows=rows.filter(p=>p.day>=start);if(end)rows=rows.filter(p=>p.day<=end);
    if(!start&&!end){const active=$('[data-v99-paper-range].active')?.dataset.v99PaperRange||'all';if(active!=='all'&&rows.length){const hours=active==='24h'?24:active==='7d'?168:720;const cutoff=rows.at(-1).time-hours*3600000;rows=rows.filter(p=>p.time>=cutoff)}}
    return rows;
  }
  function redrawPaper() {
    if(!$('#v99-paper-money')||!payload?.v99Research?.paper)return;
    const keys=selected('[data-v99-paper-engine]',ORDER).filter(k=>payload.v99Research.paper[k]);
    const money=[],roi=[],daily=[];
    for(const k of keys){const raw=paperWindowRaw(payload.v99Research.paper[k]?.curve);if(!raw.length)continue;const firstRaw=raw[0].value;const by=new Map();for(const p of raw)by.set(p.day,p);const days=[...by.values()].sort((a,b)=>a.day.localeCompare(b.day));money.push({key:k,color:COLORS[k],points:days.map(p=>({day:p.day,value:p.value}))});roi.push({key:k,color:COLORS[k],points:days.map(p=>({day:p.day,value:(p.value/firstRaw-1)*100}))});const d=[];for(let i=0;i<days.length;i++){const base=i?days[i-1].value:firstRaw;d.push({day:days[i].day,value:(days[i].value/base-1)*100})}daily.push({key:k,color:COLORS[k],points:d.slice(1)})}
    drawCategoricalBars('#v99-paper-day',daily);drawCategoricalLine('#v99-paper-money',money,'money');drawCategoricalLine('#v99-paper-pct',roi,'pct',true);
  }
  function redraw(){scheduled=false;if(!$('#v99research')?.classList.contains('active'))return;redrawBacktest();redrawPaper()}
  function schedule(){if(scheduled)return;scheduled=true;setTimeout(redraw,80)}
  async function loadData(){try{const r=await fetch(`${DATA_URL}?categorical=${Date.now()}`,{cache:'no-store'});if(r.ok){payload=await r.json();schedule()}}catch(e){console.warn('V99 categorical renderer data refresh failed',e)}}

  function boot(){loadData();const root=$('#v99research');if(root)new MutationObserver(schedule).observe(root,{childList:true,subtree:true});document.addEventListener('click',e=>{if(e.target.closest?.('#v99research'))setTimeout(schedule,120)},true);document.addEventListener('change',e=>{if(e.target.closest?.('#v99research'))setTimeout(schedule,120)},true);window.addEventListener('resize',schedule);setInterval(loadData,60000)}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
