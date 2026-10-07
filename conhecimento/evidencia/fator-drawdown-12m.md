---
tipo: evidencia
evidencia: fator/DRAWDOWN_12M
familia: PRECO
direcao_esperada: 1
cobertura: 2010-2025
disponivel_ate: 2025-12-31
fonte: [fator_valor, fator_definicao, cotacao_b3_diaria, evento_corporativo]
gerado_em: 2026-10-07
hash: cf992ae4cf4f2c516192e2394bfbede256cd3fab808c0d001fa9677e5ee8f104
---

## Resumo

Queda do pico em 12 meses (PRECO; maior é melhor). Em 21 pregões, Q5 − Q1 rendeu em média -0,3% por mês (01/2010–12/2025, n=191); o IC de 95% inclui zero: sem vantagem distinguível do acaso.

## Resultado

Spread = retorno médio do quintil 5 menos o do quintil 1; "Q5 > média" = fração das datas em que o quintil 5 superou a média do universo.

| Pregões | Período | n | Spread médio | IC 95% | Spread > 0 | Q5 > média |
|---|---|---|---|---|---|---|
| 21 | Todos | 191 | -0,3% | -1,4% a +0,9% | 55% | 50% |
| 21 | 2010–2015 | 72 | +1,1% | -0,5% a +2,8% | 62% | 57% |
| 21 | 2016–2019 | 48 | -2,5% | -4,9% a -0,1% | 44% | 38% |
| 21 | 2020–2025 | 71 | -0,2% | -2,2% a +1,8% | 55% | 51% |
| 63 | Todos | 63 | -1,3% | -5,0% a +2,4% | 54% | 49% |
| 63 | 2010–2015 | 24 | +3,0% | -1,8% a +7,8% | 62% | 58% |
| 63 | 2016–2019 | 16 | -6,9% | -12,3% a -1,6% | 31% | 31% |
| 63 | 2020–2025 | 23 | -1,9% | -9,7% a +5,9% | 61% | 52% |
| 126 | Todos | 32 | -2,4% | -8,1% a +3,3% | 47% | 47% |
| 126 | 2010–2015 | 12 | +2,9% | -6,4% a +12,2% | 50% | 58% |
| 126 | 2016–2019 | 8 | -12,3% | -22,7% a -1,9% | 38% | 38% |
| 126 | 2020–2025 | 12 | -1,1% | -10,0% a +7,8% | 50% | 42% |

## Por regime

- Mercado em alta nos 12 meses anteriores: spread médio +0,6% em 21 pregões (IC -0,6% a +1,8%, n=104).
- Mercado em baixa nos 12 meses anteriores: spread médio -1,3% em 21 pregões (IC -3,4% a +0,8%, n=87).

## Limitações

- Referência mensal (primeiro pregão do mês), última janela encerrada até 03/11/2025; nada do ano corrente.
- Universo: papéis com o fator calculado no mês (líquidos); quintil com menos de 5 papéis é descartado.
- Retorno a frente sobre preço ajustado por evento corporativo inferido (confiança ≥ 0,8); 89 eventos no banco. Retorno acima de 300% na janela é descartado como dado suspeito.
- Sem custo de transação, imposto ou liquidez de execução. Resultado passado não garante o futuro.
