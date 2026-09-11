# Identidades dos engines — decisão do proprietário em 08/09/2026

**V16 é exclusivamente Balanced Relaxed e está congelado.** Preservar sua
estratégia, parâmetros e histórico. O paper continua recebendo dados novos;
congelamento da estratégia não significa congelar os preços ou o patrimônio.
O registro de integridade está em `config/frozen_v16_manifest.json`.
O snapshot do código está em `archive/v16-balanced-relaxed-20260908`.

**V17 é a reconstrução experimental antes chamada incorretamente de V16.**
Todo desenvolvimento dessa reconstrução usa módulos, testes, configurações e
relatórios V17. Os relatórios antigos com nomes V16 continuam intactos como
evidência histórica; não se altera retroativamente a identificação dos testes.

Referências registradas, ainda não comparáveis entre si:

- V16 Balanced Relaxed: +94,82% no recorte do painel de 07/09/2025 a 07/09/2026.
- Origem do V17: experimento `boosting_12_relative_cost1`, +34,90% no recorte
  pesquisado de 01/09/2025 a 31/08/2026. Isso não demonstra melhoria sobre V16.

O objetivo é superar substancialmente V13, V14, V15, V16 e V99 em retorno e
risco, além da carteira que distribui o mesmo capital total entre V13–V16.
Não somar os ROIs individuais como se quatro capitais fossem um só.
Os limiares numéricos da configuração V17 são uma operacionalização de pesquisa,
não uma promessa de lucro nem evidência de aprovação.

Antes de qualquer afirmação de superioridade, reconciliar dados, universo,
horários, início da simulação, estado inicial, custos, funding e execução.
Usar os cinco períodos solicitados, registrar todos os resultados negativos,
testar custos/atraso/funding adversos e obter validação adicional não utilizada
na escolha do modelo. Nunca promover automaticamente por atingir números
retrospectivos. V17 permanece RESEARCH_ONLY, sem ordens reais nem paper ativo.

Reprodução: instalar `requirements-v17-research.txt` em ambiente isolado;
executar `python -m unittest discover -s tests -q`. Para gerar uma rodada V17:
`python scripts/research_v17.py --market-root <dados> --end AAAA-MM-DD
--output-dir <pasta_nova>`.
