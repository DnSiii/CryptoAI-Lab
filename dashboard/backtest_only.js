function applyBacktestBranding(){
  document.title="Backtest CryptoAI";
  const brandStrong=document.querySelector(".brand-copy strong");
  const brandSmall=document.querySelector(".brand-copy small");
  const kicker=document.querySelector(".top-kicker");
  const title=document.querySelector("#page-title");
  const subtitle=document.querySelector("#page-subtitle");
  const footer=document.querySelector(".footer span:first-child");
  if(brandStrong)brandStrong.textContent="BACKTEST";
  if(brandSmall)brandSmall.textContent="CRYPTOAI";
  if(kicker)kicker.textContent="BACKTEST · CRYPTOAI";
  if(title)title.textContent="Backtest CryptoAI";
  if(subtitle)subtitle.textContent="Análise histórica comparativa dos engines V13, V14, V15, V16 e V99.";
  if(footer)footer.textContent="Backtest CryptoAI · Historical Replay";
}

function applyViewBranding(view){
  if(view==="paper"){
    if(typeof pcApplyPaperBranding==="function")pcApplyPaperBranding();
  }else{
    applyBacktestBranding();
  }
}

/* Readability pass only: wider daily spacing, staggered data labels and
   proportional integer axes with an explicit zero on percentage charts. */
function chartNiceIntegerStep(minValue,maxValue,targetTicks=10){
  const span=Math.max(Math.abs(maxValue-minValue),1);
  const raw=span/Math.max(2,targetTicks);
  const power=Math.pow(10,Math.floor(Math.log10(raw)));
  const normalized=raw/power;
  const factor=normalized<=1?1:normalized<=2?2:normalized<=5?5:10;
  return Math.max(1,Math.round(factor*power));
}

function chartIntegerAxis(values,{includeZero=true,targetTicks=10,extraRoom=true}={}){
  let min=Math.min(...values),max=Math.max(...values);
  if(includeZero){min=Math.min(min,0);max=Math.max(max,0)}
  if(!Number.isFinite(min)||!Number.isFinite(max)){min=0;max=1}
  if(min===max){min-=1;max+=1}
  const step=chartNiceIntegerStep(min,max,targetTicks);
  let axisMin=Math.floor(min/step)*step;
  let axisMax=Math.ceil(max/step)*step;
  if(includeZero){axisMin=Math.min(axisMin,0);axisMax=Math.max(axisMax,0)}
  if(extraRoom){
    if(max>0&&axisMax-max<step*.35)axisMax+=step;
    if(min<0&&min-axisMin<step*.35)axisMin-=step;
  }
  if(axisMin===axisMax)axisMax=axisMin+step;
  const ticks=[];
  for(let v=axisMin,count=0;v<=axisMax+step*.25&&count<40;v+=step,count++)ticks.push(Math.round(v));
  return{min:axisMin,max:axisMax,step,ticks};
}

function chartAxisLabel(value,options={}){
  const v=Math.round(value);
  if(options.money)return`R$${v.toLocaleString("pt-BR")}`;
  return`${v>0?"+":""}${v}%`;
}

function chartLabelBox(ctx,text,x,y,color){
  ctx.font="9px Inter,system-ui";
  ctx.textAlign="center";
  const width=ctx.measureText(text).width+6;
  const h=12;
  ctx.fillStyle="rgba(5,8,18,.84)";
  ctx.fillRect(x-width/2,y-h+2,width,h);
  ctx.fillStyle=color||"#dce7f5";
  ctx.fillText(text,x,y);
}

ensureStage=function(stageId,pointCount,perDay=72){
  const stage=document.querySelector(stageId);if(!stage)return;
  const parent=stage.parentElement;
  const available=parent?.clientWidth||700;
  const isDaily=String(stageId).includes("daily");
  const spacing=isDaily?132:112;
  const min=Math.max(available,Math.min(52000,Math.max(900,pointCount*spacing)));
  stage.style.width=`${min}px`;
};

if(typeof pcSizeStage==="function"){
  pcSizeStage=function(id,count,px=34){
    const stage=document.querySelector(id);if(!stage)return;
    const scroller=stage.parentElement,available=Math.max(320,Math.floor(scroller?.clientWidth||800));
    const isBars=String(id).includes("hourly")||String(id).includes("daily");
    const spacing=isBars?118:104;
    const width=Math.max(available,Math.min(52000,Math.max(900,count*spacing)));
    stage.style.width=`${width}px`;
    stage.style.minWidth=`${width}px`;
    stage.style.maxWidth="none";
  };
}

drawLineChart=function(canvas,series,options={}){
  if(!series.length)return;
  const size=canvasSize(canvas);if(!size)return;
  const{ctx,width,height}=size,pad={left:74,right:34,top:64,bottom:46};
  const all=series.flatMap(s=>s.points).filter(p=>Number.isFinite(p.time)&&Number.isFinite(p.value));
  if(!all.length)return;
  const minT=Math.min(...all.map(p=>p.time)),maxT=Math.max(...all.map(p=>p.time));
  const values=all.map(p=>p.value);
  const axis=chartIntegerAxis(values,{includeZero:!options.money,targetTicks:10,extraRoom:true});
  const x=t=>pad.left+((t-minT)/Math.max(maxT-minT,1))*(width-pad.left-pad.right);
  const y=v=>pad.top+((axis.max-v)/Math.max(axis.max-axis.min,1e-9))*(height-pad.top-pad.bottom);
  ctx.clearRect(0,0,width,height);
  ctx.font="10px Inter,system-ui";
  ctx.textAlign="right";
  axis.ticks.forEach(v=>{
    const yy=y(v);
    ctx.strokeStyle=v===0?"rgba(255,255,255,.30)":"rgba(148,163,184,.10)";
    ctx.lineWidth=v===0?1.2:1;
    ctx.beginPath();ctx.moveTo(pad.left,yy);ctx.lineTo(width-pad.right,yy);ctx.stroke();
    ctx.fillStyle=v===0?"#a9b6c8":"#718198";
    ctx.fillText(chartAxisLabel(v,options),pad.left-9,yy+3);
  });
  const lanes=[-30,-15,0,15,30];
  series.forEach((s,si)=>{
    if(s.points.length<2)return;
    ctx.strokeStyle=s.color;
    ctx.lineWidth=s.key==="v99"?2.6:1.9;
    ctx.globalAlpha=s.key==="v99"?1:.82;
    ctx.beginPath();
    s.points.forEach((p,i)=>{const xx=x(p.time),yy=y(p.value);i?ctx.lineTo(xx,yy):ctx.moveTo(xx,yy)});
    ctx.stroke();ctx.globalAlpha=1;
    s.points.forEach(p=>{
      const xx=x(p.time),yy=y(p.value);
      ctx.fillStyle=s.color;ctx.beginPath();ctx.arc(xx,yy,2.5,0,Math.PI*2);ctx.fill();
      const rawY=yy+(lanes[si%lanes.length]??0);
      const labelY=Math.max(13,Math.min(height-pad.bottom-5,rawY));
      chartLabelBox(ctx,labelValue(p.value,options),xx,labelY,"#dce7f5");
      if(si===0){ctx.font="9px Inter,system-ui";ctx.fillStyle="#718198";ctx.textAlign="center";ctx.fillText(shortDate(p.time),xx,height-12)}
    });
  });
};

drawBars=function(canvas,rows,keys){
  if(!rows.length||!keys.length)return;
  const size=canvasSize(canvas);if(!size)return;
  const{ctx,width,height}=size,pad={left:68,right:26,top:58,bottom:50};
  const vals=rows.flatMap(r=>keys.map(k=>r.values[k])).filter(Number.isFinite);
  if(!vals.length)return;
  const axis=chartIntegerAxis(vals,{includeZero:true,targetTicks:10,extraRoom:true});
  const y=v=>pad.top+((axis.max-v)/Math.max(axis.max-axis.min,1e-9))*(height-pad.top-pad.bottom);
  const plotW=width-pad.left-pad.right,groupW=plotW/rows.length;
  const barW=Math.max(5,Math.min(16,(groupW*.72)/keys.length));
  ctx.clearRect(0,0,width,height);
  ctx.font="10px Inter,system-ui";ctx.textAlign="right";
  axis.ticks.forEach(v=>{
    const yy=y(v);
    ctx.strokeStyle=v===0?"rgba(255,255,255,.36)":"rgba(148,163,184,.10)";
    ctx.lineWidth=v===0?1.3:1;
    ctx.beginPath();ctx.moveTo(pad.left,yy);ctx.lineTo(width-pad.right,yy);ctx.stroke();
    ctx.fillStyle=v===0?"#a9b6c8":"#718198";
    ctx.fillText(chartAxisLabel(v),pad.left-8,yy+3);
  });
  const zy=y(0);
  rows.forEach((r,idx)=>{
    const center=pad.left+groupW*idx+groupW/2,total=barW*keys.length;
    keys.forEach((k,ki)=>{
      const v=r.values[k];if(!Number.isFinite(v))return;
      const xx=center-total/2+ki*barW,yy=y(v),top=Math.min(yy,zy),h=Math.max(1,Math.abs(zy-yy));
      ctx.fillStyle=COLORS[k];ctx.globalAlpha=k==="v99"?1:.82;
      ctx.fillRect(xx,top,Math.max(2,barW-2),h);ctx.globalAlpha=1;
      ctx.font="9px Inter,system-ui";ctx.fillStyle="#dce7f5";ctx.textAlign="center";
      ctx.save();
      ctx.translate(xx+barW/2,v>=0?top-6:top+h+11);
      ctx.rotate(-Math.PI/2);
      ctx.fillText(pct(v,1),0,0);
      ctx.restore();
    });
    ctx.font="9px Inter,system-ui";ctx.fillStyle="#718198";ctx.textAlign="center";
    ctx.fillText(shortDate(r.time),center,height-12);
  });
};

document.addEventListener("DOMContentLoaded",()=>{
  applyBacktestBranding();
  document.querySelectorAll(".nav-btn").forEach(button=>{
    button.addEventListener("click",()=>setTimeout(()=>applyViewBranding(button.dataset.view),0));
  });
  setTimeout(()=>{
    try{
      if(typeof setView==="function")setView("backtest");
      applyBacktestBranding();
    }catch(_e){}
  },180);
});
