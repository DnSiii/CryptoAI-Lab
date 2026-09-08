"""Build a transparent research checkpoint from the immutable V16 evidence."""
import json
from pathlib import Path


def main():
    root=Path(__file__).resolve().parents[1]
    reports=root/'reports'
    current=json.loads((reports/'v16_cost_batch_20260908_a/results.json').read_text())
    name='boosting_12_relative_cost1'
    chosen=current[name]
    base=chosen['scenarios']['base']['windows']
    def pct(value): return f'{value*100:+.2f}%'.replace('.',',')
    lines=['# V16 — registro de pesquisa de 08/09/2026','',
        '**Estado: EM DESENVOLVIMENTO / NÃO APROVADO. Nenhuma promoção para paper ou produção.**','',
        'O experimento abaixo é um resultado retrospectivo selecionado depois de comparar alternativas. '
        'Não é um holdout intocado nem comprovação de resultado futuro. As cinco janelas se sobrepõem.','',
        f'Identificador reproduzível: `{name}`. Corte dos testes: **31/08/2026, 23h UTC**. '
        'Os valores a seguir não representam os últimos sete dias até 08/09.','',
        '| Período | Datas UTC | Retorno líquido modelado | Queda máxima horária |',
        '|---|---|---:|---:|']
    for key,metric in base.items():
        lines.append(f"| {key} | {metric['start'][:10]} a {metric['end'][:10]} | {pct(metric['return'])} | {pct(metric['max_drawdown'])} |")
    lines+=['','Custos normais: 0,07% por lado, incluindo taxa e slippage modelados. '
        'Funding observado é aplicado às posições existentes. Sinais usam informações até o fechamento; '
        'execução ocorre na abertura seguinte. Os sinais não são operações reais.','',
        '| Cenário | Retorno no ano | Retorno em 6 meses | Queda máxima no ano |','|---|---:|---:|---:|']
    labels={'base':'Custos normais','severe_cost':'Custos de 0,12% por lado',
        'delay_3h':'Execução com duas horas adicionais de atraso',
        'adverse_funding':'Funding pago ×2 e recebido ×0,5'}
    for key,label in labels.items():
        w=chosen['scenarios'][key]['windows']
        lines.append(f"| {label} | {pct(w['1Y']['return'])} | {pct(w['6M']['return'])} | {pct(w['1Y']['max_drawdown'])} |")
    baseline=json.loads((reports/'v16_relative_batch_20260906_a/results.json').read_text())['boosting_12_relative_beta_buffer']
    earlier=baseline['scenarios']['base']['windows']['1Y']
    lines+=['','A nova regra exige que a melhora prevista ao trocar posições compense o custo adicional. '
        f"No teste anterior, a mesma família teve {pct(earlier['return'])} no ano e "
        f"{pct(baseline['scenarios']['severe_cost']['windows']['1Y']['return'])} com custos maiores. "
        'Isso motivou a hipótese de reduzir trocas de pouca utilidade. Foram mantidos quatro modelos de origem '
        'e três níveis fixos de custo, registrando também os resultados negativos.','',
        'O limiar mínimo de pesquisa já registrado era 50% no ano, 15% em seis meses, 5% em três meses, '
        'resultado positivo em 30 e 7 dias e drawdown anual de no máximo 20%, além dos testes de estresse. '
        'O resultado atual falha no requisito anual. Esse limiar é um filtro de pesquisa, não uma promessa de rentabilidade.','',
        'Limitações ainda abertas: seleção após múltiplas tentativas, sensibilidade entre modelos, '
        'universo histórico e encerramento de contratos, execução com quantidades mínimas/spread/liquidez reais, '
        'capacidade para capital agregado de clientes e validação futura com a versão congelada. '
        'Neutro em beta significa neutralidade estimada no rebalanceamento, sujeita à variação das posições entre ajustes.','',
        'A coleta separada de dados até 07/09/2026 não foi aceita como completa: FTMUSDT e MKRUSDT '
        'não retornaram funding recente. É preciso distinguir contratos inativos de falhas de coleta antes '
        'de usar essa extensão. Não se preencheu esse funding ausente com zero para aprovar o teste.','',
        '**Validação do código:** 84 testes passaram, incluindo purga dos resultados ainda desconhecidos no treinamento, '
        'mutação de dados futuros, limites de exposição, fechamento de ambas as pernas diante de indisponibilidade '
        'e custo incremental de rebalanceamento. Testes de software não demonstram lucratividade.','',
        '**Preservação:** as execuções verificaram os hashes dos insumos protegidos. '
        'V13, V14, V15, configurações oficiais, workflow do paper, dashboard e NEVRYN não foram alterados.','',
        'Protocolos, resultados completos e vereditos de cada rodada:','']
    for folder in ['v16_rebuild_batch_20260905_a','v16_forecast_batch_20260905_a',
                   'v16_relative_batch_20260906_a','v16_cost_batch_20260908_a']:
        verdict=json.loads((reports/folder/'verdict.json').read_text())
        count=verdict.get('tested',verdict.get('tested_count'))
        lines.append(f'- [{folder}]({folder}/results.json): {count} avaliações; inclui controles repetidos, quando aplicável.')
    lines+=['','Reprodução: `python -m unittest discover -s tests -q`; em seguida, '
        '`scripts/research_v16_relative.py --market-root <insumo> --forecast-batch reports/v16_forecast_batch_20260905_a '
        '--output-dir <nova_pasta> --cost-aware`. Nunca substituir uma pasta de evidência existente.','',
        'Dependências de pesquisa utilizadas: Python 3.11+, NumPy 2.3.5, pandas 2.2.3, '
        'scikit-learn 1.8.0 e threadpoolctl 3.6.0. As matrizes geradas ficam fora do Git; '
        'os protocolos mantêm hashes dos dados e das previsões de origem.','']
    path=reports/'V16_STATUS_20260908.md'
    path.write_text('\n'.join(lines))
    print(path)


if __name__=='__main__': main()
