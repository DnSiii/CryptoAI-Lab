# CryptoAI-Lab

Laboratório de pesquisa e validação do projeto CryptoAI.

## Estado atual

Este repositório nasce a partir do checkpoint recuperado em 2026-08-12. A versão de referência preservada é a **CryptoAI V12 Defensive Strategic Ensemble** (PAPER_ONLY). O laboratório ativo segue a candidata posterior **BTC/ETH Core + Funding Carry causal** em futuros USD-M.

### Regra de promoção congelada

Uma candidata só pode avançar se, em replay causal/walk-forward líquido e sem vazamento:

- CAGR base > 50% a.a.
- max drawdown <= 35% (ou muito próximo, somente com justificativa quantitativa)
- custos severos > 35% a.a.
- atraso adicional de +3h > 40% a.a.
- >= 10 decisões de posição/mês
- risco de ruína bootstrap < 1%
- sobreviver às 24 fases horárias de rebalanceamento
- sem liquidação/ruína nos cenários testados
- robustez a funding adverso, custo extremo, universo com contratos deslistados e remoção de ativos

O objetivo não é maximizar taxa de acerto. É maximizar crescimento composto líquido: perder pouco quando errado, ganhar muito quando certo e reinvestir, evitando probabilidade irresponsável de ruína.

## Segurança

- **PAPER_ONLY / RESEARCH_ONLY**
- execução real bloqueada
- nenhuma chave de API é necessária para pesquisa histórica pública
- qualquer integração de execução deverá nascer desligada por padrão e separada do motor de pesquisa

## Próximo ciclo

1. Preservar integralmente o checkpoint recuperado.
2. Reconstruir um replay causal reproduzível com dados oficiais de futuros USD-M e funding.
3. Rodar contraprovas de custos, atraso, 24 horários, contratos deslistados, funding adverso, bootstrap e liquidação.
4. Tentar quebrar a candidata antes de pesquisar melhorias.
5. Só promover uma nova versão após passar todos os gates congelados.
