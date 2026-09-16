/* Performer chart viewport policy.
   7D/30D fit the available panel width. Longer windows expand only inside
   .chart-scroll, so the document itself never needs horizontal scrolling. */
(function () {
  window.ensureStage = function ensureStage(stageId, pointCount, perDay = 30) {
    const stage = document.querySelector(stageId);
    if (!stage) return;

    const scroller = stage.parentElement;
    const available = Math.max(320, Math.floor(scroller?.clientWidth || stage.clientWidth || 900));
    const count = Math.max(1, Number(pointCount) || 1);

    let width = available;
    if (count > 31) {
      const pxPerDay = Math.max(24, Math.min(46, Number(perDay) || 30));
      width = Math.max(available, Math.min(16000, count * pxPerDay));
    }

    stage.style.width = `${Math.round(width)}px`;
    stage.style.minWidth = `${Math.round(width)}px`;
    stage.style.maxWidth = 'none';
  };

  const refit = () => {
    document.querySelectorAll('.chart-stage').forEach((stage) => {
      const scroller = stage.parentElement;
      if (!scroller) return;
      if (stage.scrollWidth < scroller.clientWidth || stage.getBoundingClientRect().width < scroller.clientWidth) {
        stage.style.width = `${scroller.clientWidth}px`;
        stage.style.minWidth = `${scroller.clientWidth}px`;
      }
    });
  };

  window.addEventListener('resize', () => requestAnimationFrame(refit));

  if (!document.querySelector('script[data-v99-categorical]')) {
    const script = document.createElement('script');
    script.src = `v99_categorical.js?v=20260916g-${Date.now()}`;
    script.defer = true;
    script.dataset.v99Categorical = '1';
    document.head.appendChild(script);
  }
})();
