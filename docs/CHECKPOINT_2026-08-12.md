# CryptoAI checkpoint — 2026-08-12

## Baseline preservada

A V12 foi congelada como **CryptoAI V12 Defensive Strategic Ensemble**, apenas para paper/research. Métricas recuperadas: ~22,02% CAGR, max DD ~-23,26%, Sharpe ~1,03. Ela continua como referência defensiva, não como meta final.

## Candidata que estava em pesquisa quando o repositório foi criado

**BTC/ETH Core + Funding Carry causal**, Binance USD-M Futures, long/short, candles de 1h e funding histórico real.

Fatos recuperados do experimento anterior:

- horizontes simultâneos: 60/90/120/150 dias;
- sleeve de funding: 35% por padrão, 85% quando dominava o bloco de regime;
- universo começou com 10 contratos e foi ampliado para 48, incluindo contratos deslistados;
- replay exato reportado: 56,1% a.a. líquido, DD -27,9%;
- atraso adicional de 3h: 52,0% a.a.;
- custos severos: 37,1% a.a.;
- 24 fases horárias: 55,2% a 62,7% a.a., DD aproximadamente -25% a -28%;
- sizing reduzido: 52,5% a.a., DD -26,3%, custos severos 35,1% a.a., bootstrap de ruína 0,582%;
- sem liquidação simulada no cenário reportado.

## Régua congelada

A candidata não pode ser promovida por “parecer boa”. Deve passar simultaneamente:

- exact/walk-forward base >50% CAGR líquido;
- DD <=35% ou extremamente próximo com justificativa quantitativa;
- custos severos >35% CAGR;
- atraso de +3h >40% CAGR;
- >=10 decisões/mês;
- risco bootstrap de ruína <1%;
- 24/24 fases de rebalanceamento robustas;
- sem liquidação/ruína;
- stress de funding, custo extremo, remoção de ativos e survivorship bias.

## Lacuna de recuperação

O ZIP e o código-fonte exato da candidata anterior não ficaram acessíveis. Portanto, **não é permitido fingir que uma implementação nova é o mesmo algoritmo** apenas porque usa os mesmos rótulos. Este repositório preserva os resultados como checkpoint histórico e inicia uma reconstrução causal independente. Só podemos dizer “reproduzido” se o código novo recuperar as métricas em dados reais de forma independente.

## Próximo passo correto

O ponto de continuidade é tentar quebrar a candidata com contratos antigos/deslistados, custos e funding adversos e, ao mesmo tempo, eliminar a lacuna de reprodutibilidade. Se a reconstrução não recuperar o edge, ela é rejeitada e a pesquisa volta para descoberta de estratégia — sem capital real.
