---
tipo: evidencia
evidencia: fator/MOMENTO_12_1
familia: PRECO
direcao_esperada: 1
cobertura: 2010-2025
disponivel_ate: 2025-12-31
fonte: [fator_valor, fator_definicao, cotacao_b3_diaria, evento_corporativo]
gerado_em: 2026-10-07
hash: 8838f20004491f7621bb6548fbad1dc7a07a724d515520bf98fbd0b58396a033
---

## Resumo

Retorno de 12 meses excluindo o ultimo mes (PRECO; maior é melhor). Em 21 pregões, Q5 − Q1 rendeu em média +0,2% por mês (02/2010–12/2025, n=190); o IC de 95% inclui zero: sem vantagem distinguível do acaso.

## Resultado

Spread = retorno médio do quintil 5 menos o do quintil 1; "Q5 > média" = fração das datas em que o quintil 5 superou a média do universo.

| Pregões | Período | n | Spread médio | IC 95% | Spread > 0 | Q5 > média |
|---|---|---|---|---|---|---|
| 21 | Todos | 190 | +0,2% | -0,9% a +1,2% | 58% | 54% |
| 21 | 2010–2015 | 71 | +1,3% | -0,1% a +2,8% | 65% | 52% |
| 21 | 2016–2019 | 48 | -1,7% | -4,2% a +0,8% | 46% | 50% |
| 21 | 2020–2025 | 71 | +0,2% | -1,5% a +2,0% | 59% | 59% |
| 63 | Todos | 63 | +0,3% | -2,5% a +3,2% | 62% | 52% |
| 63 | 2010–2015 | 24 | +3,9% | +0,0% a +7,8% | 71% | 62% |
| 63 | 2016–2019 | 16 | -6,8% | -13,1% a -0,5% | 38% | 31% |
| 63 | 2020–2025 | 23 | +1,6% | -2,7% a +5,9% | 70% | 57% |
| 126 | Todos | 31 | -3,2% | -10,8% a +4,4% | 48% | 35% |
| 126 | 2010–2015 | 12 | +2,2% | -8,1% a +12,4% | 67% | 33% |
| 126 | 2016–2019 | 8 | -16,5% | -37,2% a +4,2% | 25% | 38% |
| 126 | 2020–2025 | 11 | +0,5% | -8,2% a +9,3% | 45% | 36% |

## Por regime

- Mercado em alta nos 12 meses anteriores: spread médio +0,6% em 21 pregões (IC -0,5% a +1,8%, n=103).
- Mercado em baixa nos 12 meses anteriores: spread médio -0,4% em 21 pregões (IC -2,3% a +1,5%, n=87).

## Limitações

- Referência mensal (primeiro pregão do mês), última janela encerrada até 03/11/2025; nada do ano corrente.
- Universo: papéis com o fator calculado no mês (líquidos); quintil com menos de 5 papéis é descartado.
- Retorno a frente sobre preço ajustado por evento corporativo inferido (confiança ≥ 0,8); 89 eventos no banco. Retorno acima de 300% na janela é descartado como dado suspeito.
- Sem custo de transação, imposto ou liquidez de execução. Resultado passado não garante o futuro.
