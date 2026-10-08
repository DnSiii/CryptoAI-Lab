/* V98 Independent Lab: information-only dashboard.
 * The V98 source is strictly its own branch. Do not import V99 data or
 * use other engines as inputs to V98 model selection.
 */
(function(){
  'use strict';
  const ROOT='https://github.com/DnSiii/CryptoAI-Lab/tree/research/v98-independent-zero';
  const RAW='https://raw.githubusercontent.com/DnSiii/CryptoAI-Lab/research/v98-independent-zero';
  const STATE_URL=RAW+'/state/v98_independent_state.json';
  const SLOTS=[
    ['growth_core','Growth Core','Motor de crescimento direcional'],
    ['opportunity','Opportunity','Oportunidades assimétricas'],
    ['relative_value','Relative Value','Estratégias de valor relativo'],
    ['stress_recovery','Stress / Recovery','Recuperação e cenários adversos'],
    ['regime_router','Regime Router','Roteamento conforme o mercado'],
    ['dynamic_allocator','Dynamic Allocator','Alocação dinâmica e causal'],
    ['risk_governor','Risk Governor','Controle de concentração e ruína'],
  ];
  const EVIDENCE=[
    {phase:'240',kind:'Rejeitada',title:'Recuperação de choque idiossincrático',description:'8 especificações rejeitadas; resultado isolado de treino não constitui motor V98.',path:'research/v98_independent/phase240_postmortem.md'},
    {phase:'241',kind:'Preregistrada',title:'Deslocamento entre volume e preço',description:'Hipótese e critérios congelados; resultados de desempenho ainda não confirmados no estado atual.',path:'research/v98_independent/phase241_prereg.md'},
    {phase:'242',kind:'Preregistrada',title:'Reversão por impacto de preço / liquidez',description:'Implementação auditada; sem desempenho validado no checkpoint consultado.',path:'research/v98_independent/phase242_prereg.md'},
    {phase:'243',kind:'Arquitetura',title:'Construção do motor completo',description:'Inventário das evidências V98 e definição dos sete módulos antes do backtest do sistema.',path:'research/v98_independent/phase243_engine_architecture_prereg.md'},
  ];
  const $=(selector,root=document)=>root.querySelector(selector);
  const $$=(selector,root=document)=>Array.from(root.querySelectorAll(selector));
  const safe=value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const source=path=>ROOT+'/'+path;
  let remoteState=null,tab='backtest',lastFetch=0,pending=null,loadError=null;
  function statusText(value){
    return ({
      needs_inventory:'Inventário pendente',
      needs_new_research_or_inventory:'Requer pesquisa',
      empty:'Sem componente aprovado',
      candidate:'Candidato em análise',
      frozen:'Congelado para validação',
      validation_pass:'Validação aprovada',
    })[value]||String(value||'Status ainda não definido').replace(/_/g,' ');
  }
  function markTab(){
    $$('[data-v98-tab]').forEach(button=>{
      const active=button.dataset.v98Tab===tab;
      button.classList.toggle('active',active);
      button.setAttribute('aria-selected',String(active));
      button.setAttribute('aria-pressed',String(active));
    });
    for(const name of ['backtest','paper']){
      const pane=$('#v98-'+name);
      if(pane)pane.classList.toggle('active',tab===name);
    }
  }
  function header(){
    document.title='CryptoAI · V98 Independent Lab';
    const title=$('#page-title'),sub=$('#page-subtitle'),kick=$('.top-kicker');
    if(title)title.textContent='V98 · Independent Lab';
    if(sub)sub.textContent='Pesquisa independente · arquitetura e validações do motor V98';
    if(kick)kick.textContent='CRYPTOAI · V98 RESEARCH';
    const foot=$('.footer span:first-child');
    if(foot)foot.textContent='CryptoAI · V98 Independent Lab · RESEARCH ONLY';
  }
  function summaryCard(title,value,caption){
    return '<article class="v99-insight"><span>'+safe(title)+'</span><strong>'+safe(value)+'</strong><small>'+safe(caption)+'</small></article>';
  }
  function renderBacktest(){
    const box=$('#v98-backtest');if(!box)return;
    if(!remoteState){
      box.innerHTML='<div class="v99-empty">'+(loadError?
        'Não foi possível consultar a branch V98. Nenhum dado de pesquisa foi inventado.':'Carregando o estado real da pesquisa V98…')+
        '</div><article class="v99-panel"><a class="v98-source-link" href="'+ROOT+'" target="_blank" rel="noopener noreferrer">Consultar branch V98 no GitHub ↗</a></article>';
      return;
    }
    const st=remoteState,slots=st.architecture_slots||{},ch=st.champion;
    const champion=ch?(typeof ch==='string'?ch:'Candidato em avaliação'):'Nenhum';
    const phase=String(st.phase||'Não informado').replaceAll('_',' ');
    box.innerHTML=
      '<div class="v99-note"><strong>Pesquisa, não trading ao vivo.</strong> As fases anteriores são estudos individuais e não representam um motor completo validado. Esta área consulta somente a branch V98, respeitando a independência do projeto.</div>'+
      '<div class="v99-insights">'+
      summaryCard('Etapa atual',phase,'Estado oficial do V98 Independent')+
      summaryCard('Campeão',champion,ch?'Consultar aprovação antes de comparar':'Nenhum motor completo promovido')+
      summaryCard('Holdout',st.holdout_locked?'Bloqueado':'Verificar liberação','Não utilizado para ajustar hipóteses')+
      summaryCard('Arquitetura','7 módulos','Em inventário e construção')+
      '</div>'+
      '<article class="v99-panel"><div class="v99-panel-head"><div><p>CONSTRUÇÃO DO MOTOR</p><h3>Arquitetura V98</h3></div><small>Fonte: estado da branch independente</small></div>'+
      '<p class="v98-state-note">Cada componente só pode ser incluído com evidência da própria pesquisa V98, sem ressuscitar hipóteses rejeitadas nem usar resultados do V99 para escolher parâmetros.</p>'+
      '<div class="v98-slot-grid">'+SLOTS.map(([key,label,desc])=>
        '<div class="v98-slot"><strong>'+safe(label)+'</strong><small>'+safe(desc)+'</small><small class="v98-status-pending">'+safe(statusText(slots[key]))+'</small></div>'
      ).join('')+'</div>'+
      '<a class="v98-source-link" href="'+source('research/v98_independent/phase243_engine_architecture_prereg.md')+'" target="_blank" rel="noopener noreferrer">Ler especificação da arquitetura ↗</a></article>'+
      '<article class="v99-panel"><div class="v99-panel-head"><div><p>HISTÓRICO CIENTÍFICO</p><h3>Fases documentadas</h3></div><small>Sem misturar backtest isolado com motor aprovado</small></div>'+
      '<div class="v99-table-wrap"><table class="v99-table"><thead><tr><th>Fase</th><th>Hipótese / desenvolvimento</th><th>Estado</th><th>Evidência</th></tr></thead><tbody>'+
      EVIDENCE.map(row=>'<tr><td>Phase '+row.phase+'</td><td><strong>'+safe(row.title)+'</strong><div class="v98-state-note">'+safe(row.description)+'</div></td><td>'+safe(row.kind)+'</td><td><a class="v98-source-link" target="_blank" rel="noopener noreferrer" href="'+source(row.path)+'">Abrir ↗</a></td></tr>').join('')+
      '</tbody></table></div></article>'+
      '<article class="v99-panel"><div class="v99-panel-head"><div><p>PRÓXIMOS GATES</p><h3>Do projeto ao motor validado</h3></div></div>'+
      '<p class="v98-state-note">Inventário das evidências → módulos elegíveis → sistema V98 preregistrado → treino cronológico → custos base/severe/supersevere → regimes e risco → validação separada → holdout futuro. Não há garantia de promoção.</p>'+
      '<a class="v98-source-link" href="'+source('research/v98_independent/V98_NORTH_STAR.md')+'" target="_blank" rel="noopener noreferrer">Objetivo e regras do V98 ↗</a></article>'+
      '<div class="v99-note">Atualização da pesquisa obtida diretamente do GitHub. <button type="button" id="v98-refresh" class="v99-chip">Atualizar estado</button></div>';
    $('#v98-refresh')?.addEventListener('click',()=>load(true));
  }
  function renderPaper(){
    const box=$('#v98-paper');if(!box)return;
    const ch=remoteState?.champion;
    box.innerHTML=
      '<article class="v99-paper-hero"><div><p class="eyebrow">V98 · PAPER TRADING INDEPENDENTE</p><h2>Paper completo</h2>'+
      '<p>Área reservada para acompanhar o V98 após a promoção científica de um motor completo. Aqui não entram simulações fictícias nem resultados dos outros candidatos.</p></div>'+
      '<div class="v99-paper-status"><span>Execução</span><strong class="v98-status-risk">NÃO INICIADA</strong><small>Sem paper V98 oficial publicado</small></div></article>'+
      '<div class="v99-insights">'+
      summaryCard('Capital simulado','—','Aguardando motor V98 validado')+
      summaryCard('ROI forward','—','Nenhuma série forward verificada')+
      summaryCard('Operações','—','Sem operações V98 publicadas')+
      summaryCard('Status do motor',ch?'Verificação necessária':'Em pesquisa','Holdout protegido')+
      '</div>'+
      '<article class="v99-panel"><div class="v99-panel-head"><div><p>EVOLUÇÃO DO CAPITAL E ROI</p><h3>Gráficos de paper</h3></div><small>Sem dados publicados</small></div>'+
      '<div class="v99-empty">Ainda não existe uma curva forward oficial de um V98 completo. Quando houver paper verificável, este painel poderá receber gráficos por hora/dia, patrimônio e drawdown.</div></article>'+
      '<article class="v99-panel"><div class="v99-panel-head"><div><p>POSIÇÕES E OPERAÇÕES</p><h3>Histórico do V98</h3></div></div>'+
      '<div class="v99-empty">Nenhuma ordem real e nenhum histórico de paper V98 comprovado. Não é apropriado substituir isso por PnL histórico ou dados do V99.</div></article>'+
      '<article class="v99-panel"><div class="v99-panel-head"><div><p>CRITÉRIOS DE ATIVAÇÃO</p><h3>Proteções necessárias</h3></div></div>'+
      '<p class="v98-state-note">Exigir motor completo congelado, treino temporal positivo com custos realistas, testes severos, auditoria de causalidade, validação separada e autorização de paper sem ordens reais.</p>'+
      '<a class="v98-source-link" href="'+ROOT+'" target="_blank" rel="noopener noreferrer">Acompanhar pesquisa independente no GitHub ↗</a></article>';
  }
  function render(){
    if(!$('#v98research')?.classList.contains('active'))return;
    markTab();
    if(tab==='paper')renderPaper();else renderBacktest();
  }
  async function load(force=false){
    if(pending)return pending;
    if(!force&&remoteState&&Date.now()-lastFetch<300000){render();return;}
    const url=STATE_URL+'?dashboard='+Date.now();
    pending=(async()=>{
      try{
        const response=await fetch(url,{cache:'no-store'});
        if(!response.ok)throw new Error('HTTP '+response.status);
        const value=await response.json();
        if(value?.engine!=='V98 Independent'||value?.branch!=='research/v98-independent-zero')throw new Error('Incompatible V98 research state');
        remoteState=value;lastFetch=Date.now();loadError=null;
      }catch(error){loadError=error;console.warn('V98 Independent state not available',error)}
      finally{pending=null;render();}
    })();
    return pending;
  }
  function show(){
    $$('.view').forEach(view=>view.classList.toggle('active',view.id==='v98research'));
    $$('.nav-btn').forEach(button=>button.classList.toggle('active',button.dataset.view==='v98research'));
    header();
    markTab();
    render();
    load();
  }
  function init(){
    const section=$('#v98research');
    if(!section)return;
    const button=$('.nav-btn[data-view="v98research"]');
    if(button)button.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();show()},true);
    $$('[data-v98-tab]',section).forEach(button=>button.addEventListener('click',()=>{
      tab=button.dataset.v98Tab==='paper'?'paper':'backtest';
      render();
    }));
  }
  window.V98Research={render,show,reload:()=>load(true)};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
