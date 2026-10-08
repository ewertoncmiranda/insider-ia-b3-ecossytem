---
tipo: fundamentos
colecao: formulas
titulo: Sinal tecnico de serie
origem: painel-ativos-frontend/public/js/pages/FormulasPage.js
disponivel_ate: 2000-01-01
gerado_em: 2026-10-08
hash: ebda4316b44eaa117da2512a5f728737b4856abe889f6a88ec5266a87c967696
---

## Resumo

Tendencia e anomalia estatistica nos ultimos 20 candles coletados.

- **Fonte dos dados:** BRAPI /historical - gratis, limitado a 3 meses / candle diario

## Sinal de momentum

Tendencia confirmada por volume: compra tecnica com preco acima da media movel e volume acima da media; venda tecnica no inverso.

- **Fórmula:** compra se preco > MM20 e volume / volume medio > 1.3; venda se preco < MM20 e essa razao < 0.7
- **Situação:** implementado
- **Contextos de uso:** Day trade

## Sinal de reversao

Extremo estatistico: compra tecnica em desconto anormal perto da minima de 52 semanas; venda tecnica em sobrecompra perto da maxima.

- **Fórmula:** compra se z-score 1.5 ou preco a <=5% da maxima 52s
- **Situação:** implementado
- **Contextos de uso:** Swing / reversão
