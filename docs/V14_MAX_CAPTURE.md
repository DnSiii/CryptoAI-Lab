# CryptoAI V14 — Máxima Captura

## Objetivo congelado

A V14 maximiza o patrimônio composto líquido no histórico, sem meta ou teto
mensal. Retorno não é reduzido por ser “alto demais”; risco, causalidade,
custos e ausência de ruína são restrições obrigatórias.

V13 e o paper anterior de oportunidades permanecem preservados. A V14 abre
uma quarta trilha, com fronteira forward própria e capital simulado inicial de
R$ 10.000.

## Seleção histórica

Foram testadas 84 combinações de sinal, orçamento e disjuntor. Vinte e nove
ficaram dentro da restrição-base de drawdown máximo de 35% e sem ruína exata.
O líder selecionado apresentou:

- patrimônio terminal de 54,0072 vezes o inicial;
- drawdown máximo-base de 32,50%;
- 214 episódios de oportunidade independentes;
- 48 episódios encerrados acima de 4%, 33 acima de 8%, 19 acima de 15%, 15
  acima de 20%, 7 acima de 30% e 2 acima de 40%;
- melhor episódio encerrado em +66,03%.

Um episódio começa quando o sleeve de oportunidades é ativado e termina quando
ele fica inativo. Intervalos de até 24 horas são unidos, portanto episódios não
se sobrepõem e a mesma alta não é contada repetidamente.

## Configuração promovida somente ao paper

- V13 congelada preservada como núcleo;
- sinal de impulso com limiar de 1,5%;
- exposição adicional máxima de 22,5%;
- exposição-alvo total máxima de 157,5%;
- disjuntor em queda de 18%, reduzindo a exposição para 60% por 168 horas;
- custos-base de 0,07% por lado, funding e execução na abertura seguinte;
- nenhuma credencial e nenhum método de ordem real.

## Limite da evidência

O líder foi escolhido depois de pesquisar o mesmo histórico. Isso cria risco de
overfitting: os números históricos não são promessa nem holdout virgem. O paper
forward existe justamente para descobrir quanto dessa vantagem sobrevive em
dados realmente novos. No cenário histórico severo combinado, o patrimônio
continuou positivo, mas o drawdown chegou a 42,3%.
