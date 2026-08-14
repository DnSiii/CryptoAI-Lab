# CryptoAI V13 — laboratório agressivo com controle de ruína

Este laboratório é separado da V12 defensiva. O objetivo congelado é maximizar
o crescimento composto líquido, aceitando risco calculado, posições compradas e
vendidas e alavancagem dinâmica, sem transformar preservação de capital em meta
principal.

Regras de pesquisa:

- sinais somente após candle fechado;
- execução no candle seguinte;
- taxas, slippage e funding incluídos;
- preços de futuros USD-M, não proxy Spot;
- busca separada da avaliação walk-forward;
- liquidação, exposição e risco de ruína explicitamente simulados;
- nenhuma função de ordem real;
- resultados negativos preservados.

Régua provisória para um candidato chegar ao paper:

- CAGR walk-forward líquido de pelo menos 50% ao ano;
- drawdown walk-forward de no máximo 35%;
- retorno positivo em pelo menos 75% dos anos/blocos fora da amostra;
- atividade média de pelo menos 10 decisões de posição por mês;
- CAGR de pelo menos 35% com custos e slippage severos;
- risco de ruína estimado abaixo de 1% no dimensionamento promovido;
- nenhuma dependência de um único ativo, ano ou parâmetro estreito.

Essa régua é um critério de pesquisa, não promessa de retorno.

## Paper V13 automatizado

O workflow `CryptoAI V13 hourly paper` executa no GitHub Actions a cada hora,
no minuto 17, e também pode ser iniciado manualmente. Ele:

- usa exclusivamente endpoints públicos de klines e funding da Binance USD-M;
- preserva o candidato congelado e o corte forward de 13/08/2026 19:00 UTC;
- não usa API key, segredo, saldo ou método de envio de ordem;
- exige BTC e ETH atualizados até o último candle horário encerrado;
- mantém o histórico canônico em cache diário e publica snapshots compactos na
  branch `paper-results`;
- interrompe o ciclo se testes, atualidade dos dados ou trava `PAPER_ONLY`
  falharem.

O primeiro ciclo sem cache reconstrói o histórico público e pode demorar mais.
Os ciclos seguintes baixam somente os dados novos. O computador do usuário não
precisa permanecer ligado.
