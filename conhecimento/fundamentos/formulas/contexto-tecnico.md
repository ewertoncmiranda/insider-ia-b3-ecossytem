---
tipo: fundamentos
colecao: formulas
titulo: Contexto tecnico do dia
origem: painel-ativos-frontend/public/js/pages/FormulasPage.js
disponivel_ate: 2000-01-01
gerado_em: 2026-10-08
hash: 16f90579fc08c1cd0834d1576e70a3e84cd155c057ad6f495b80c593168aa231
---

## Resumo

Onde o preco de hoje esta dentro da propria historia recente do ativo.

- **Fonte dos dados:** BRAPI /quote - gratis (fiftyTwoWeekLow/High, regularMarketDayHigh/Low)

## Posicao no range de 52 semanas

0% = minima das 52 semanas, 100% = maxima. Zona "Proximo da minima" (=85%) ou "Meio do range".

- **Fórmula:** posicao = (preco - minima 52s) / (maxima 52s - minima 52s)
- **Situação:** implementado
- **Contextos de uso:** Swing / reversão; Longo prazo

## Variacoes intradiarias

Variacao desde a abertura, contra o fechamento anterior e amplitude entre maxima e minima do dia.

- **Fórmula:** variacao = (preco atual - referencia) / referencia
- **Situação:** implementado
- **Contextos de uso:** Day trade
