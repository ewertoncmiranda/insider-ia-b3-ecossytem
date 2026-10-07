---
tipo: evidencia
evidencia: fator/LIQUIDEZ_63D
familia: PRECO
direcao_esperada: 1
cobertura: 2010-2025
disponivel_ate: 2025-12-31
fonte: [fator_valor, fator_definicao, cotacao_b3_diaria, evento_corporativo]
gerado_em: 2026-10-07
hash: 1eeb3bfd4c1d0d75e408b62665af7e90041de22339f39f11d21377d757158765
---

## Resumo

Volume financeiro medio diario em 63 pregoes (PRECO; maior é melhor). Em 21 pregões, Q5 − Q1 rendeu em média -0,1% por mês (01/2010–12/2025, n=191); o IC de 95% inclui zero: sem vantagem distinguível do acaso.

## Resultado

Spread = retorno médio do quintil 5 menos o do quintil 1; "Q5 > média" = fração das datas em que o quintil 5 superou a média do universo.

| Pregões | Período | n | Spread médio | IC 95% | Spread > 0 | Q5 > média |
|---|---|---|---|---|---|---|
| 21 | Todos | 191 | -0,1% | -0,8% a +0,5% | 51% | 46% |
| 21 | 2010–2015 | 72 | -0,8% | -1,8% a +0,3% | 49% | 39% |
| 21 | 2016–2019 | 48 | +0,1% | -1,3% a +1,6% | 56% | 48% |
| 21 | 2020–2025 | 71 | +0,3% | -0,5% a +1,1% | 51% | 51% |
| 63 | Todos | 63 | -0,7% | -2,7% a +1,3% | 51% | 43% |
| 63 | 2010–2015 | 24 | -1,8% | -4,8% a +1,1% | 42% | 38% |
| 63 | 2016–2019 | 16 | +0,2% | -4,0% a +4,3% | 44% | 31% |
| 63 | 2020–2025 | 23 | -0,2% | -3,7% a +3,4% | 65% | 57% |
| 126 | Todos | 32 | -3,8% | -7,5% a -0,1% | 38% | 34% |
| 126 | 2010–2015 | 12 | -7,6% | -13,4% a -1,8% | 33% | 17% |
| 126 | 2016–2019 | 8 | -2,6% | -10,7% a +5,5% | 25% | 25% |
| 126 | 2020–2025 | 12 | -0,8% | -6,5% a +4,9% | 50% | 58% |

## Por regime

- Mercado em alta nos 12 meses anteriores: spread médio -0,9% em 21 pregões (IC -1,7% a -0,1%, n=104).
- Mercado em baixa nos 12 meses anteriores: spread médio +0,8% em 21 pregões (IC -0,1% a +1,7%, n=87).

## Limitações

- Referência mensal (primeiro pregão do mês), última janela encerrada até 03/11/2025; nada do ano corrente.
- Universo: papéis com o fator calculado no mês (líquidos); quintil com menos de 5 papéis é descartado.
- Retorno a frente sobre preço ajustado por evento corporativo inferido (confiança ≥ 0,8); 89 eventos no banco. Retorno acima de 300% na janela é descartado como dado suspeito.
- Sem custo de transação, imposto ou liquidez de execução. Resultado passado não garante o futuro.
