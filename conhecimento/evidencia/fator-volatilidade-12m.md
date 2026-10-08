---
tipo: evidencia
evidencia: fator/VOLATILIDADE_12M
familia: PRECO
direcao_esperada: -1
cobertura: 2010-2025
disponivel_ate: 2025-12-31
fonte: [fator_valor, fator_definicao, cotacao_b3_diaria, evento_corporativo]
gerado_em: 2026-10-07
hash: 83476a642f596a5bb0cb3581e1cc8ae2b6ce1c796caaae60217e3a2ead4b318a
---

## Resumo

Desvio-padrao anualizado dos retornos diarios em 12 meses (PRECO; menor é melhor). Em 21 pregões, Q5 − Q1 rendeu em média +0,2% por mês (01/2010–12/2025, n=191); o IC de 95% inclui zero: sem vantagem distinguível do acaso.

## Resultado

Spread = retorno médio do quintil 5 menos o do quintil 1; "Q5 > média" = fração das datas em que o quintil 5 superou a média do universo.

| Pregões | Período | n | Spread médio | IC 95% | Spread > 0 | Q5 > média |
|---|---|---|---|---|---|---|
| 21 | Todos | 191 | +0,2% | -0,9% a +1,4% | 54% | 59% |
| 21 | 2010–2015 | 72 | +1,5% | -0,1% a +3,2% | 58% | 61% |
| 21 | 2016–2019 | 48 | -2,0% | -4,4% a +0,5% | 44% | 52% |
| 21 | 2020–2025 | 71 | +0,4% | -1,6% a +2,4% | 58% | 61% |
| 63 | Todos | 63 | +0,7% | -2,9% a +4,4% | 56% | 56% |
| 63 | 2010–2015 | 24 | +4,6% | -0,3% a +9,5% | 67% | 67% |
| 63 | 2016–2019 | 16 | -4,7% | -9,4% a -0,0% | 31% | 44% |
| 63 | 2020–2025 | 23 | +0,5% | -7,1% a +8,1% | 61% | 52% |
| 126 | Todos | 32 | -0,2% | -6,6% a +6,2% | 41% | 53% |
| 126 | 2010–2015 | 12 | +6,7% | -3,1% a +16,6% | 58% | 67% |
| 126 | 2016–2019 | 8 | -15,9% | -24,5% a -7,3% | 0% | 12% |
| 126 | 2020–2025 | 12 | +3,3% | -6,8% a +13,3% | 50% | 67% |

## Por regime

- Mercado em alta nos 12 meses anteriores: spread médio +0,7% em 21 pregões (IC -0,6% a +1,9%, n=104).
- Mercado em baixa nos 12 meses anteriores: spread médio -0,3% em 21 pregões (IC -2,4% a +1,7%, n=87).

## Limitações

- Referência mensal (primeiro pregão do mês), última janela encerrada até 03/11/2025; nada do ano corrente.
- Universo: papéis com o fator calculado no mês (líquidos); quintil com menos de 5 papéis é descartado.
- Retorno a frente sobre preço ajustado por evento corporativo inferido (confiança ≥ 0,8); 89 eventos no banco. Retorno acima de 300% na janela é descartado como dado suspeito.
- Sem custo de transação, imposto ou liquidez de execução. Resultado passado não garante o futuro.
