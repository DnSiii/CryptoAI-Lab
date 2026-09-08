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

document.addEventListener("DOMContentLoaded",()=>{
  applyBacktestBranding();
  const timer=setInterval(()=>{
    try{
      if(typeof setView==="function"){
        setView("backtest");
        applyBacktestBranding();
        const cards=document.querySelector("#backtest-kpis");
        if(cards&&cards.children.length){
          clearInterval(timer);
        }
      }
    }catch(_e){}
  },80);
  setTimeout(()=>clearInterval(timer),12000);
});
