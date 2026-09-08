document.addEventListener("DOMContentLoaded",()=>{
  const timer=setInterval(()=>{
    try{
      if(typeof setView==="function"){
        setView("backtest");
        const cards=document.querySelector("#backtest-kpis");
        if(cards&&cards.children.length){
          clearInterval(timer);
        }
      }
    }catch(_e){}
  },80);
  setTimeout(()=>clearInterval(timer),12000);
});
