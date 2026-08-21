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

- usa exclusivamente arquivos públicos oficiais e verificados por checksum da
  Binance USD-M;
- preserva o candidato congelado e o corte forward de 13/08/2026 19:00 UTC;
- não usa API key, segredo, saldo ou método de envio de ordem;
- exige BTC e ETH dentro da janela máxima de 48 horas prevista para a
  publicação dos arquivos diários oficiais;
- mantém o histórico canônico em cache diário e publica snapshots compactos na
  branch `paper-results`;
- interrompe o ciclo se testes, atualidade dos dados ou trava `PAPER_ONLY`
  falharem.

O primeiro ciclo sem cache reconstrói o histórico público e pode demorar mais.
Os ciclos seguintes consultam somente os arquivos diários ainda não incorporados.
O workflow verifica a publicação a cada hora, mas os novos candles entram no
paper quando o arquivo diário oficial fica disponível. O computador do usuário
não precisa permanecer ligado.

## Paper V14 Máxima Captura

A V14 preserva V13 e Turbo e acrescenta uma quarta carteira paper, selecionada
para maximizar patrimônio final sem teto mensal artificial. A configuração,
resultados por episódios independentes e limitações estão em
[`docs/V14_MAX_CAPTURE.md`](docs/V14_MAX_CAPTURE.md). A V14 continua
`PAPER_ONLY`; dinheiro real permanece bloqueado.
