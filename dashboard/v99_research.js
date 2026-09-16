/* Dedicated V99 research lab. Kept separate from the official V99 Frozen view. */
(function () {
  const DATA_URL = 'https://raw.githubusercontent.com/DnSiii/CryptoAI-Lab/paper-results/dashboard/dashboard_data.json';
  const ORDER = ['r98', 'f1', 'f3', 'f7', 'f12'];
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const brl = (value) => Number(value || 0).toLocaleString('pt-BR', {style:'currency', currency:'BRL'});
  const pct = (value, digits = 2) => `${Number(value || 0) >= 0 ? '+' : ''}${Number(value || 0).toFixed(digits).replace('.', ',')}%`;
  const num = (value, digits = 3) => value == null ? '—' : Number(value).toFixed(digits).replace('.', ',');
  const dt = (value) => value ? new Intl.DateTimeFormat('pt-BR', {day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit', timeZone:'America/Sao_Paulo'}).format(new Date(value)) : '—';
  const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (m) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  let data = null;
  let activeTab = 'backtest';

  function installStyles() {
    if ($('#v99-research-styles')) return;
    const style = document.createElement('style');
    style.id = 'v99-research-styles';
    style.textContent = `
      #v99research{padding-bottom:28px}.v99r-hero{display:flex;justify-content:space-between;gap:24px;align-items:flex-end;padding:28px;border:1px solid rgba(183,255,74,.18);border-radius:22px;background:linear-gradient(135deg,rgba(183,255,74,.08),rgba(53,214,232,.04));margin-bottom:18px}.v99r-hero h2{margin:5px 0 8px;font-size:clamp(26px,3vw,42px)}.v99r-hero p{max-width:850px;color:var(--muted,#94a3b8);line-height:1.55}.v99r-badge{white-space:nowrap;border:1px solid rgba(183,255,74,.32);border-radius:999px;padding:10px 14px;color:#b7ff4a;font-weight:800}.v99r-tabs{display:flex;gap:8px;margin:14px 0 18px}.v99r-tab{border:1px solid rgba(148,163,184,.18);background:rgba(255,255,255,.025);color:#aebbd0;border-radius:12px;padding:11px 18px;font-weight:800;cursor:pointer}.v99r-tab.active{background:rgba(183,255,74,.12);border-color:rgba(183,255,74,.42);color:#dfffaa}.v99r-pane{display:none}.v99r-pane.active{display:block}.v99r-note{padding:13px 16px;border-radius:14px;background:rgba(95,140,255,.07);border:1px solid rgba(95,140,255,.17);color:#b9c8db;margin-bottom:16px;line-height:1.5}.v99r-grid{display:grid;grid-template-columns:repeat(5,minmax(180px,1fr));gap:12px;margin:14px 0 20px}.v99r-card{padding:18px;border-radius:18px;border:1px solid rgba(148,163,184,.13);background:rgba(8,13,25,.72);min-width:0}.v99r-card.leader{border-color:rgba(183,255,74,.42);box-shadow:0 0 0 1px rgba(183,255,74,.07) inset}.v99r-card .top{display:flex;justify-content:space-between;gap:8px;align-items:center}.v99r-card .top strong{font-size:14px}.v99r-status{font-size:10px;border-radius:999px;padding:4px 7px;background:rgba(148,163,184,.10);color:#9fb0c6;text-transform:uppercase}.v99r-status.leader{background:rgba(183,255,74,.12);color:#b7ff4a}.v99r-main{font-size:28px;font-weight:900;margin:13px 0 2px}.v99r-main.positive{color:#b7ff4a}.v99r-main.negative{color:#ff7d91}.v99r-sub{font-size:12px;color:#7f91a8;margin-bottom:15px;min-height:32px}.v99r-kv{display:grid;grid-template-columns:1fr 1fr;gap:8px}.v99r-kv div{padding:9px;border-radius:11px;background:rgba(255,255,255,.025)}.v99r-kv span{display:block;font-size:10px;color:#71839a;text-transform:uppercase;margin-bottom:3px}.v99r-kv strong{font-size:13px}.v99r-panel{border:1px solid rgba(148,163,184,.13);background:rgba(8,13,25,.65);border-radius:18px;padding:18px;margin-top:14px}.v99r-panel h3{margin:0 0 4px}.v99r-panel>p{margin:0 0 14px;color:#7f91a8}.v99r-table-wrap{overflow:auto}.v99r-table{width:100%;border-collapse:collapse;min-width:900px}.v99r-table th,.v99r-table td{text-align:left;padding:11px 10px;border-bottom:1px solid rgba(148,163,184,.09);font-size:12px}.v99r-table th{color:#6f8299;text-transform:uppercase;font-size:10px}.v99r-table tr.leader td{background:rgba(183,255,74,.035)}.v99r-positive{color:#b7ff4a;font-weight:800}.v99r-negative{color:#ff7d91;font-weight:800}.v99r-empty{padding:26px;text-align:center;color:#8394aa;border:1px dashed rgba(148,163,184,.18);border-radius:16px}.v99r-boundary{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px}.v99r-boundary span{padding:8px 11px;border-radius:999px;background:rgba(255,255,255,.035);font-size:11px;color:#9cafc5}.v99r-pos{font-size:11px;color:#8ca0b8;margin-top:8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}@media(max-width:1200px){.v99r-grid{grid-template-columns:repeat(2,minmax(220px,1fr))}}@media(max-width:700px){.v99r-grid{grid-template-columns:1fr}.v99r-hero{align-items:flex-start;flex-direction:column}.v99r-badge{white-space:normal}}
    `;
    document.head.appendChild(style);
  }

  function installView() {
    if ($('#v99research')) return;
    const nav = $('.nav');
    if (nav) {
      const button = document.createElement('button');
      button.className = 'nav-btn v99r-nav';
      button.dataset.view = 'v99research';
      button.innerHTML = '<span class="nav-symbol">V</span><div><strong>V99</strong><small>Research Lab</small></div>';
      nav.appendChild(button);
      button.addEventListener('click', (event) => {
        event.preventDefault();
        showView();
      });
    }
    const footer = $('.footer');
    const section = document.createElement('section');
    section.id = 'v99research';
    section.className = 'view';
    section.innerHTML = `
      <article class="v99r-hero">
        <div><p class="eyebrow">V99 · RESEARCH LAB</p><h2>Cinco versões. Um mesmo paper.</h2><p>R98, R106 F1, F3, F7/F9 e F12 acompanhados lado a lado. O backtest permanece como referência congelada; o paper começa no mesmo boundary para todos e não recalibra nenhuma versão.</p></div>
        <div class="v99r-badge">PAPER ONLY · 0 ORDENS REAIS</div>
      </article>
      <div class="v99r-tabs"><button class="v99r-tab active" data-v99-tab="backtest">Backtest</button><button class="v99r-tab" data-v99-tab="paper">Paper</button></div>
      <div id="v99r-backtest" class="v99r-pane active"></div>
      <div id="v99r-paper" class="v99r-pane"></div>
    `;
    if (footer) footer.parentElement.insertBefore(section, footer);
    else $('.main')?.appendChild(section);
    $$('.v99r-tab', section).forEach((button) => button.addEventListener('click', () => setTab(button.dataset.v99Tab)));
  }

  function showView() {
    $$('.view').forEach((view) => view.classList.toggle('active', view.id === 'v99research'));
    $$('.nav-btn').forEach((button) => button.classList.toggle('active', button.dataset.view === 'v99research'));
    const title = $('#page-title');
    const subtitle = $('#page-subtitle');
    if (title) title.textContent = 'V99 · Research Lab';
    if (subtitle) subtitle.textContent = 'Backtest validado e paper forward das cinco melhores versões do V99.';
    render();
  }

  function setTab(tab) {
    activeTab = tab;
    $$('.v99r-tab').forEach((button) => button.classList.toggle('active', button.dataset.v99Tab === tab));
    $('#v99r-backtest')?.classList.toggle('active', tab === 'backtest');
    $('#v99r-paper')?.classList.toggle('active', tab === 'paper');
  }

  function researchStatus(item) {
    const gate = item?.researchGate || item?.researchStatus || '';
    if (String(gate).includes('LEADER') || gate === 'research_leader') return ['Líder atual', 'leader'];
    if (gate === 'REFERENCE' || gate === 'reference') return ['Referência', ''];
    return ['Pesquisa', ''];
  }

  function btCard(key, item) {
    const [status, statusClass] = researchStatus(item);
    return `<article class="v99r-card ${key === 'f7' ? 'leader' : ''}"><div class="top"><strong>${esc(item.label || key.toUpperCase())}</strong><span class="v99r-status ${statusClass}">${status}</span></div><div class="v99r-main positive">${pct(item.historicalRoiPct)}</div><div class="v99r-sub">${esc(item.name || '')}</div><div class="v99r-kv"><div><span>Holdout</span><strong>${pct(item.holdoutRoiPct)}</strong></div><div><span>Max DD</span><strong>${pct(item.maxDrawdownPct)}</strong></div><div><span>PF</span><strong>${num(item.profitFactor)}</strong></div><div><span>Payoff</span><strong>${num(item.payoff, 2)}</strong></div></div></article>`;
  }

  function renderBacktest(v99) {
    const root = $('#v99r-backtest');
    if (!root) return;
    const bt = v99?.backtest || {};
    if (!Object.keys(bt).length) {
      root.innerHTML = '<div class="v99r-empty">Aguardando o primeiro snapshot do V99 Research Lab.</div>';
      return;
    }
    const rows = ORDER.filter((key) => bt[key]).map((key) => {
      const item = bt[key];
      return `<tr class="${key === 'f7' ? 'leader' : ''}"><td><strong>${esc(item.label)}</strong><br><small>${esc(item.name)}</small></td><td class="v99r-positive">${pct(item.historicalRoiPct)}</td><td class="v99r-positive">${pct(item.holdoutRoiPct)}</td><td>${pct(item.maxDrawdownPct)}</td><td>${num(item.profitFactor)}</td><td>${item.winRatePct == null ? '—' : pct(item.winRatePct)}</td><td>${item.positiveDaysPct == null ? '—' : pct(item.positiveDaysPct)}</td><td>${num(item.payoff,2)}</td><td>${item.severeRoiPct == null ? '—' : pct(item.severeRoiPct)}</td></tr>`;
    }).join('');
    root.innerHTML = `<div class="v99r-note"><strong>Leitura correta:</strong> estes números são o snapshot de backtest/holdout já validado. Eles ficam congelados para comparação e não são recalculados para favorecer o paper.</div><div class="v99r-grid">${ORDER.filter((key) => bt[key]).map((key) => btCard(key, bt[key])).join('')}</div><article class="v99r-panel"><h3>Comparativo completo</h3><p>F7/F9 é o campeão de pesquisa atual. F1, F3 e F12 permanecem no paper como adversários fixos, mesmo tendo sido rejeitados nos gates anteriores.</p><div class="v99r-table-wrap"><table class="v99r-table"><thead><tr><th>Versão</th><th>Histórico</th><th>Holdout</th><th>Max DD</th><th>PF</th><th>WR</th><th>Dias +</th><th>Payoff</th><th>Severe</th></tr></thead><tbody>${rows}</tbody></table></div></article>`;
  }

  function paperCard(key, item) {
    const [status, statusClass] = researchStatus(item);
    const roiClass = Number(item.roiPct || 0) >= 0 ? 'positive' : 'negative';
    const positions = (item.positions || []).slice(0,3).map((p) => `${p.symbol.replace('USDT','')} ${p.direction === 'buy' ? 'L' : 'S'} ${Number(p.weightPct).toFixed(1)}%`).join(' · ');
    return `<article class="v99r-card ${key === 'f7' ? 'leader' : ''}"><div class="top"><strong>${esc(item.label || key.toUpperCase())}</strong><span class="v99r-status ${statusClass}">${status}</span></div><div class="v99r-main ${roiClass}">${pct(item.roiPct,4)}</div><div class="v99r-sub">${brl(item.currentCapitalBrl)} · ${Number(item.newForwardHours || 0)}h forward</div><div class="v99r-kv"><div><span>Resultado</span><strong>${brl(item.netResultBrl)}</strong></div><div><span>Exposição</span><strong>${pct(item.grossExposurePct,1)}</strong></div><div><span>Máximo</span><strong>${brl(item.highestCapitalBrl)}</strong></div><div><span>Mínimo</span><strong>${brl(item.lowestCapitalBrl)}</strong></div></div><div class="v99r-pos">${positions || 'Sem posição aberta agora'}</div></article>`;
  }

  function renderPaper(v99) {
    const root = $('#v99r-paper');
    if (!root) return;
    const paper = v99?.paper || {};
    if (!Object.keys(paper).length) {
      root.innerHTML = '<div class="v99r-empty">O paper das cinco versões está inicializando. Assim que o primeiro ciclo publicar, os cinco começam juntos em R$ 10.000.</div>';
      return;
    }
    const rows = ORDER.filter((key) => paper[key]).map((key) => {
      const item = paper[key];
      const c = Number(item.roiPct || 0) >= 0 ? 'v99r-positive' : 'v99r-negative';
      return `<tr class="${key === 'f7' ? 'leader' : ''}"><td><strong>${esc(item.label)}</strong></td><td class="${c}">${pct(item.roiPct,4)}</td><td>${brl(item.currentCapitalBrl)}</td><td>${brl(item.netResultBrl)}</td><td>${pct(item.grossExposurePct,1)}</td><td>${item.positions?.length || 0}</td><td>${Number(item.newForwardHours || 0)}h</td><td>${dt(item.latest)}</td></tr>`;
    }).join('');
    root.innerHTML = `<div class="v99r-boundary"><span>Boundary comum: <strong>${dt(v99.paperStart)}</strong></span><span>Último dado: <strong>${dt(v99.latest)}</strong></span><span>Capital inicial: <strong>R$ 10.000 por versão</strong></span><span>Seleção congelada antes do paper: <strong>${v99.selectionFrozenBeforePaper ? 'SIM' : 'NÃO'}</strong></span></div><div class="v99r-note"><strong>Forward-only:</strong> todos começaram no mesmo instante. O resultado abaixo não contém o lucro histórico do backtest e nenhuma versão é recalibrada pelos dados do paper.</div><div class="v99r-grid">${ORDER.filter((key) => paper[key]).map((key) => paperCard(key, paper[key])).join('')}</div><article class="v99r-panel"><h3>Placar do paper V99</h3><p>Comparação direta das cinco versões desde o mesmo boundary.</p><div class="v99r-table-wrap"><table class="v99r-table"><thead><tr><th>Versão</th><th>ROI paper</th><th>Capital</th><th>Resultado</th><th>Exposição</th><th>Posições</th><th>Forward</th><th>Atualizado</th></tr></thead><tbody>${rows}</tbody></table></div></article>`;
  }

  function render() {
    const v99 = data?.v99Research;
    renderBacktest(v99);
    renderPaper(v99);
    setTab(activeTab);
  }

  async function load() {
    try {
      const response = await fetch(`${DATA_URL}?t=${Date.now()}`, {cache:'no-store'});
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
      data = await response.json();
    } catch (error) {
      console.warn('V99 research remote snapshot failed', error);
      try {
        const response = await fetch(`dashboard_data.json?t=${Date.now()}`, {cache:'no-store'});
        data = await response.json();
      } catch (fallbackError) {
        console.warn('V99 research local snapshot failed', fallbackError);
      }
    }
    render();
  }

  installStyles();
  installView();
  load();
})();
