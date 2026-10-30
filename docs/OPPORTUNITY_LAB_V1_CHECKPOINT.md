# CryptoAI — checkpoint da camada de oportunidades V1

## Decisão

O candidato histórico passou o portão para **proposta de paper forward
separado**. Ele não foi incorporado ao paper V13, não está ativo e não possui
capacidade de enviar ordens reais.

A V13 continua congelada como core. A camada nova usa um orçamento adicional
máximo de 7,5% de exposição bruta e combina duas fases causais de entrada
(0 e 2) para reduzir dependência de uma hora específica.

## Resultado histórico exato

Período comparável: janeiro de 2021 a julho de 2026. Todo o histórico já
participou de pesquisas anteriores; portanto, isto é evidência adversarial, não
um holdout intocado.

| Cenário | CAGR V13 | CAGR combinado | Patrimônio final relativo | Drawdown combinado |
|---|---:|---:|---:|---:|
| Base | 60,14% | 67,40% | 1,416x | -28,20% |
| Custos severos | 48,82% | 50,68% | 1,171x | -31,60% |
| Atraso de 3h | 56,15% | 57,04% | 1,138x | -28,54% |
| Atraso de 6h | 46,60% | 52,00% | 1,367x | -28,62% |
| Funding adverso | 46,81% | 48,20% | 1,151x | -29,40% |
| Custos + funding adversos | 34,81% | 37,38% | 1,199x | -34,45% |

“Patrimônio final relativo” divide o patrimônio terminal do combinado pelo
patrimônio terminal da V13 no mesmo cenário. Não é o retorno de um único mês.

## Janelas rápidas observadas

No replay-base da carteira combinada, as melhores janelas históricas foram
+19,47% em 2 dias, +28,34% em 3 dias, +39,98% em 7 dias, +47,97% em 14 dias e
+55,23% em 30 dias. Esses máximos demonstram que o sistema não possui teto de
retorno; não são promessa nem frequência esperada.

Em todas as janelas de 7 dias, 1,58% atingiram pelo menos +20%. Em 14 dias,
6,42% atingiram pelo menos +20%; em 30 dias, 16,43%. Também existiram períodos
negativos: a pior janela de 30 dias foi -21,20%.

## Robustez de parâmetros

O ensemble final foi repetido em nove configurações vizinhas, alterando uma
coisa por vez: tendência, cooldown, limiar e duração máxima.

- 8 de 9 configurações passaram todos os portões (88,9%; mínimo exigido 70%);
- nenhuma apresentou ruína em nenhum cenário obrigatório;
- o pior patrimônio terminal relativo foi 0,9768x (mínimo exigido 0,90x);
- a única falha foi o filtro de tendência de 240h, que ficou 2,32% abaixo da
  V13 sob custos severos e ultrapassou marginalmente o limite de drawdown no
  cenário combinado.

## Configuração proposta

- sinal: impulso de preço e volume, execução no próximo open;
- rompimento/retorno: 48h;
- volume recente: 24h contra mediana de 336h, mínimo 2x;
- tendência direcional: 336h;
- duas fases de rebalanceamento: 0 e 2, com pesos iguais;
- máximo de duas posições por direção;
- stop inicial: 3%; trailing stop: 20%; duração máxima: 168h;
- cooldown: 24h;
- orçamento bruto da oportunidade: 0,075x;
- teto bruto combinado: 1,425x; guard de drift: 1,575x;
- circuit breaker compartilhado: drawdown de 15%, metade da exposição por 14
  dias.

## Próximo portão

Criar uma trilha de paper com nova fronteira temporal e três placares separados:
V13, oportunidade isolada no tamanho realmente alocado e carteira combinada.
Somente dados posteriores ao congelamento do candidato poderão promover ou
rejeitar a camada. Até lá, a V13 permanece o único paper oficial.
