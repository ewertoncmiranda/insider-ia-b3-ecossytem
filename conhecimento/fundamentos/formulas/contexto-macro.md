---
tipo: fundamentos
colecao: formulas
titulo: Contexto macroeconomico
origem: painel-ativos-frontend/public/js/pages/FormulasPage.js
disponivel_ate: 2000-01-01
gerado_em: 2026-10-08
hash: cd2309454b2be78fa22c0c78c8169ba7ad739f9b2dbd2602703af1eaab85c359
---

## Resumo

Um earnings yield de 8% e otimo com Selic a 6% e ruim com Selic a 14% - a classificacao fixa por si so ignora isso.

- **Fonte dos dados:** API SGS do Banco Central (api.bcb.gov.br) - gratis, sem chave. Ver a serie em Indices.

## Earnings yield vs. taxa livre de risco

Mede o quanto o earnings yield da acao compensa (ou nao) o risco extra frente a simplesmente deixar o dinheiro na Selic. Selic buscada 1x/dia e cacheada (indice_macro); nunca ao vivo na hora do clique.

- **Fórmula:** premio de risco = earnings yield do ativo - taxa Selic anual (o mais recente ponto de indice_macro)
- **Situação:** implementado
- **Contextos de uso:** Contexto macro; Longo prazo
