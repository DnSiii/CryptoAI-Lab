# V98 A3 — análise econômica anual do replay congelado (11/11/2026)

**Estado:** auditoria retrospectiva; NÃO é validação independente, NÃO aprova promoção. Fonte exclusiva: artefato GitHub Actions `13819914098`, execução `42941324822`, commit congelado `2b43253c485ef705cc7f4bcce50dad0a450cedbd`. Universo Clean-4; 27.048 horas. Nenhum dado de 2026+ foi consultado. Sem ajuste de sinais, parâmetros ou pesos.

## Reconciliação anual (USD)

Cada linha é obtida somando os campos horários do arquivo `replay/compound_ledger_{1.0,2.0,4.0}.json`. PnL líquido = gap + intrabar + funding − custo de execução; diferença de reconciliação arredondada a zero.

| Custo | Ano | Capital inicial | Capital final | Retorno | PnL bruto (gap + intrabar) | Funding | Custo execução | Giro |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1x | 2023 | 10.000,00 | 15.057,83 | 50,58% | 5.509,60 | -280,21 | 171,57 | 285.952,95 |
| 1x | 2024 | 15.057,83 | 19.080,65 | 26,72% | 5.023,72 | -689,28 | 311,61 | 519.355,24 |
| 1x | 2025 | 19.080,65 | 20.523,30 | 7,56% | 1.785,83 | -75,92 | 267,26 | 445.427,74 |
| 2x | 2023 | 10.000,00 | 14.838,10 | 48,38% | 5.455,80 | -277,13 | 340,56 | 283.801,89 |
| 2x | 2024 | 14.838,10 | 18.461,01 | 24,42% | 4.903,94 | -672,58 | 608,46 | 507.050,38 |
| 2x | 2025 | 18.461,01 | 19.583,87 | 6,08% | 1.709,04 | -72,67 | 513,51 | 427.923,82 |
| 4x | 2023 | 10.000,00 | 14.408,06 | 44,08% | 5.350,14 | -271,10 | 670,97 | 279.571,57 |
| 4x | 2024 | 14.408,06 | 17.281,03 | 19,94% | 4.673,44 | -640,44 | 1.160,04 | 483.348,53 |
| 4x | 2025 | 17.281,03 | 17.831,40 | 3,18% | 1.564,88 | -66,59 | 947,93 | 394.971,04 |

**Diagnóstico causal limitado:** a queda de 2025 decorre principalmente da redução do PnL bruto (de US$ 5.023,72 em 2024 para US$ 1.785,83 em 2025 no cenário 1x), não de aumento dos custos totais: funding + execução consumiram US$ 1.000,89 em 2024 contra US$ 343,18 em 2025. Essa decomposição é contábil, não identifica a causa econômica/regime da perda de alpha.

## Distribuição mensal 2025, custos 1x

| Mês | Retorno | PnL bruto USD | Funding USD | Execução USD |
|---|---:|---:|---:|---:|
| Jan | -1,97% | -355,51 | +14,01 | 34,32 |
| Fev | -12,60% | -2.340,58 | +10,53 | 26,48 |
| Mar | -0,97% | -170,04 | +16,87 | 4,94 |
| Abr | +6,53% | +1.058,92 | +15,43 | 16,92 |
| Mai | +6,71% | +1.215,27 | -33,12 | 24,90 |
| Jun | -0,35% | -17,99 | -15,97 | 29,67 |
| Jul | +7,23% | +1.399,45 | -46,69 | 27,36 |
| Ago | +6,96% | +1.450,86 | -48,04 | 33,58 |
| Set | +3,48% | +791,49 | -31,13 | 28,64 |
| Out | -0,61% | -146,02 | +42,12 | 28,86 |
| Nov | -5,02% | -1.081,86 | +2,15 | 6,79 |
| Dez | -0,12% | -18,15 | -2,08 | 4,79 |

Fevereiro e novembro de 2025 concentram perdas brutas importantes. Não usar esses meses para resgatar thresholds ou recalibrar o A3 congelado.

## Auditoria dos sete slots

Em `slots.csv`, 108.192 linhas (4 ativos × 27.048 horas), `regime_router` é **sempre 1,0** (uma única configuração observada), e `risk_governor` é **sempre 0,4** (uma única configuração observada). `dynamic_allocator` assume cinco valores distintos; 95.424 linhas têm valor 1,0. Isso **não prova** ausência de lógica interna, mas impede afirmar com base nesse artefato que router e governor adaptam dinamicamente a regimes e risco. Exigir inspeção causal do código e evidência operacional por regime antes de aprovar a arquitetura completa.

Média absoluta por linha, por ano: Growth Core 0,07589 / 0,08087 / 0,06932; Opportunity 0,00473 / 0,00748 / 0,00503; Relative Value 0,01623 / 0,01670 / 0,01592; Stress Recovery 0,00507 / 0,00779 / 0,00582 (2023/2024/2025). Valores representam magnitudes de slots, **não** contribuições econômicas ou prova de causalidade.

## Gates e decisão

`chronological_gate.json` registra `independent_validation=false`, `promotion_eligible=false`, e informa que resultados de histórico completo foram observados antes do gate. `reproducibility_lock.json` também registra validação independente falsa. Não reclassificar 2024/2025 como holdout intocado. Nenhuma comparação externa V14/V15/V99 autorizada. A3 **experimental / não promovido**.

**Próximo caminho crítico:** (1) verificar código causal e se router/governor têm comportamento adaptativo efetivo; (2) preparar avaliação prospectiva verdadeiramente independente com código/parametrização congelados, fontes autenticadas e sem acesso para seleção; (3) executar métricas completas, custos severos, drawdown/tails e critérios preregistrados. Sem essa evidência, não existe campeão V98 validado.
