---
tipo: fundamentos
colecao: glossario
titulo: Os indicadores
origem: painel-ativos-frontend/public/js/pages/GlossarioPage.js
disponivel_ate: 2000-01-01
gerado_em: 2026-10-08
hash: ef6be842aafb67f72630d8175c4521cd66ff84d6cd098a17aeaeafa5c009c400
---

## Resumo

Cada um responde uma pergunta diferente, e nenhum decide sozinho. Faixa boa varia muito por setor.

## LPA

Lucro liquido dividido pelo numero de acoes.

- **Sigla:** Lucro por acao
- **Pergunta para estudo:** Quanto de lucro cabe a cada acao?
- **Referência:** Compare so com o historico da propria empresa.

## VPA

Patrimonio liquido dividido pelo numero de acoes.

- **Sigla:** Valor patrimonial por acao
- **Pergunta para estudo:** Quanto de patrimonio cabe a cada acao?

## P/L

Preco da acao dividido pelo LPA.

- **Sigla:** Preco sobre lucro
- **Pergunta para estudo:** Em quantos anos o lucro atual paga o preco da acao?
- **Onde aparece no painel:** Calculado na hora, cruzando o LPA do balanco com a cotacao atual.
- **Referência:** Entre 8 e 15 costuma ser normal. Muito baixo as vezes e armadilha.

## P/VP

Preco da acao dividido pelo VPA.

- **Sigla:** Preco sobre valor patrimonial
- **Pergunta para estudo:** Estou pagando quanto por cada R$ 1 de patrimonio?
- **Referência:** Abaixo de 1 significa pagar menos que o patrimonio contabil.

## ROE

Lucro liquido dividido pelo patrimonio liquido, em %.

- **Sigla:** Retorno sobre o patrimonio liquido
- **Pergunta para estudo:** A empresa rende bem sobre o dinheiro dos socios?
- **Referência:** Acima de 15% e considerado bom.

## ROIC

Lucro da operacao ja descontado o imposto, dividido por todo o capital empregado (dos socios e dos bancos).

- **Sigla:** Retorno sobre o capital investido
- **Pergunta para estudo:** E o retorno sobre todo o capital, nao so o dos socios?
- **Onde aparece no painel:** O mais fraco dos nossos indicadores: usa aliquota nominal de 34%.
- **Referência:** Precisa superar o custo da divida para a alavancagem valer a pena.

## NOPAT

EBIT multiplicado por (1 menos a aliquota de imposto).

- **Onde aparece no painel:** Numerador do ROIC.

## Margem liquida

Lucro liquido dividido pela receita, em %.

- **Pergunta para estudo:** De cada R$ 100 vendidos, quanto vira lucro?
- **Referência:** Varia enormemente: supermercado ~2%, software ~30%.

## Earnings yield

LPA dividido pelo preco, em %. E o inverso do P/L.

- **Pergunta para estudo:** Facilita comparar a acao com a Selic.

## Dividend yield

Dividendos pagos no ano divididos pelo preco, em %.

- **Pergunta para estudo:** Quanto a acao paga de renda por ano?

## Beta

Mede o quanto a acao balanca em relacao a bolsa inteira. Acima de 1, oscila mais que o mercado.

## TTM

Os ultimos 12 meses corridos, em vez do ano fechado no calendario.

- **Sigla:** Trailing twelve months
- **Onde aparece no painel:** IMPORTANTE: nossos numeros sao do exercicio fechado, nao TTM. E a principal razao de eles diferirem de sites como o Fundamentus - em empresa de lucro volatil a diferenca passa de 40%.
