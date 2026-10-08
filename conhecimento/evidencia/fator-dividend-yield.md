---
tipo: evidencia
evidencia: fator/DIVIDEND_YIELD
familia: VALOR
direcao_esperada: 1
cobertura: 2011-2025
disponivel_ate: 2025-12-31
fonte: [fator_valor, fator_definicao, cotacao_b3_diaria, evento_corporativo]
gerado_em: 2026-10-07
hash: ed2b3250f5516914fe47962b77721ea36da8bba2fc030f47c6cbe6643ce015d1
---

## Resumo

Proventos por acao em 12 meses (DVA) sobre preco (VALOR; maior é melhor). Em 21 pregões, Q5 − Q1 rendeu em média +0,1% por mês (02/2011–12/2025, n=176); o IC de 95% inclui zero: sem vantagem distinguível do acaso.

## Resultado

Spread = retorno médio do quintil 5 menos o do quintil 1; "Q5 > média" = fração das datas em que o quintil 5 superou a média do universo.

| Pregões | Período | n | Spread médio | IC 95% | Spread > 0 | Q5 > média |
|---|---|---|---|---|---|---|
| 21 | Todos | 176 | +0,1% | -0,7% a +1,0% | 50% | 49% |
| 21 | 2010–2015 | 57 | +0,1% | -1,5% a +1,8% | 51% | 42% |
| 21 | 2016–2019 | 48 | -0,5% | -1,9% a +0,8% | 42% | 44% |
| 21 | 2020–2025 | 71 | +0,5% | -0,9% a +2,0% | 55% | 58% |
| 63 | Todos | 58 | -0,4% | -3,1% a +2,4% | 48% | 47% |
| 63 | 2010–2015 | 19 | +0,4% | -5,2% a +6,1% | 47% | 42% |
| 63 | 2016–2019 | 16 | -2,9% | -6,8% a +1,0% | 31% | 31% |
| 63 | 2020–2025 | 23 | +0,8% | -3,6% a +5,1% | 61% | 61% |
| 126 | Todos | 28 | -1,8% | -6,9% a +3,4% | 50% | 43% |
| 126 | 2010–2015 | 9 | -5,8% | -15,8% a +4,3% | 44% | 22% |
| 126 | 2016–2019 | 8 | -4,1% | -14,0% a +5,8% | 25% | 50% |
| 126 | 2020–2025 | 11 | +3,3% | -3,9% a +10,4% | 73% | 55% |

## Por regime

- Mercado em alta nos 12 meses anteriores: spread médio +0,7% em 21 pregões (IC -0,4% a +1,9%, n=89).
- Mercado em baixa nos 12 meses anteriores: spread médio -0,5% em 21 pregões (IC -1,8% a +0,8%, n=87).

## Limitações

- Referência mensal (primeiro pregão do mês), última janela encerrada até 03/11/2025; nada do ano corrente.
- Universo: papéis com o fator calculado no mês (líquidos); quintil com menos de 5 papéis é descartado.
- Retorno a frente sobre preço ajustado por evento corporativo inferido (confiança ≥ 0,8); 89 eventos no banco. Retorno acima de 300% na janela é descartado como dado suspeito.
- Sem custo de transação, imposto ou liquidez de execução. Resultado passado não garante o futuro.
