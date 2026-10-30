# CryptoAI — protocolo Core + Oportunidades

## Objetivo permanente

O objetivo é maximizar o patrimônio final composto, líquido de taxas e
funding, ao longo do tempo. Não existe meta, faixa ou teto mensal de retorno.
Uma oportunidade pode durar horas, dias ou semanas, e o sistema pode ficar sem
operar quando não houver vantagem observável.

Risco é uma restrição do problema, não a meta de retorno. O laboratório rejeita
alternativas cujo ganho dependa de risco de ruína, atraso irreal, custos
subestimados ou concentração não declarada.

## Arquitetura que não pode ser confundida

1. **Core V13 congelado:** continua produzindo exatamente os próprios alvos e
   mantém seu paper independente.
2. **Camada de oportunidades:** pesquisa sinais raros e mais rápidos em um
   orçamento de risco separado.
3. **Carteira combinada:** adiciona somente a oportunidade aprovada ao core,
   sem reduzir silenciosamente o core para fabricar um resultado melhor.
4. **Três placares:** Core V13, Oportunidades isoladas e Core + Oportunidades.

Nenhuma experiência deste laboratório pode alterar a configuração congelada,
o estado ou o histórico do paper V13.

## O que significa “melhor”

A classificação começa pelo patrimônio terminal composto, não pela média
mensal. Em seguida são impostas restrições de sobrevivência e honestidade:

- resultado após taxas e funding;
- execução causal no próximo preço disponível;
- nenhum uso de informação futura;
- nenhum caso de ruína no replay exato obrigatório;
- drawdown histórico não pior que 35%, nem mais de 5 pontos percentuais pior
  que o core sem uma revisão explícita;
- custos severos, atrasos de 3 e 6 horas e funding adverso;
- estabilidade em períodos diferentes e configurações vizinhas;
- nova trilha de paper forward antes de qualquer capital.

Uma configuração não é aprovada apenas por ter um mês extraordinário. Da mesma
forma, um mês extraordinário nunca é cortado só porque ultrapassou um número
pré-definido.

## Famílias iniciais de oportunidade

- impulso confirmado por preço e volume;
- expansão de volatilidade com rompimento;
- distorções extremas de funding;
- aceleração coordenada entre ativos líquidos.

O protótipo histórico de impulso é apenas uma referência inicial. Ele mostrou
que movimentos de 10% a 30% em janelas curtas podem aparecer no histórico, mas
a vantagem combinada perdeu força sob atraso e custos severos. Portanto, não é
oportunidade promovida nem substitui a V13.

## Fases de pesquisa

1. Reproduzir o core congelado e registrar seu patrimônio em todos os cenários.
2. Avaliar cada família isoladamente, inclusive períodos sem sinal.
3. Adicionar a oportunidade ao core usando somente o orçamento reservado e a
   capacidade livre do portfólio.
4. Comparar terminal, drawdown, custos, recuperação e distribuições de 2, 3, 7,
   14 e 30 dias.
5. Repetir em cenários adversos, vizinhanças de parâmetros e recortes de tempo.
6. Rejeitar ou registrar o candidato; não esconder tentativas que falharam.
7. Somente um candidato robusto ganha uma nova trilha de paper independente.

## Estado atual

O Core V13 permanece o único paper oficial. A camada de oportunidades está em
laboratório histórico e não possui autorização nem código de ordens reais.
