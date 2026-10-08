---
tipo: fundamentos
colecao: formulas
titulo: Valuation fundamentalista
origem: painel-ativos-frontend/public/js/pages/FormulasPage.js
disponivel_ate: 2000-01-01
gerado_em: 2026-10-08
hash: 1380189ec7bef715b396de45c0c9a68a6277c65157645f5a6ac2cb82824cc818
---

## Resumo

Quanto a acao custa hoje frente ao que a empresa entrega de lucro.

- **Fonte dos dados:** BRAPI /quote (priceEarnings, earningsPerShare) + CVM (LPA/VPA de varios anos) + Selic (indice_macro) - tudo gratis

## Preco justo por Graham ajustado por juros (3 cenarios)

Formula revisada de Graham (1974): o multiplo classico e multiplicado por 4,4/Y, onde Y e a Selic meta vigente. Sem esse ajuste, com juros de dois digitos, o preco justo sai varias vezes inflado (correcao de 27-09-2026 - ver Glossario). O cenario sem ajuste (Y=4,4) continua calculado so como referencia historica, fora da recomendacao.

- **Fórmula:** fator = 4,4 / Selic; multiplo = (8,5 + 2 x crescimento) x fator; preco justo = LPA_normalizado x multiplo; margem = (preco justo - preco atual) / preco justo
- **Situação:** implementado
- **Contextos de uso:** Longo prazo

## LPA normalizado

O LPA usado no valuation e o menor entre o atual e a media dos ultimos 3 a 5 exercicios entregues a CVM - evita que uma ciclica no pico do lucro pareca barata so por causa do ano.

- **Fórmula:** LPA_usado = min(LPA_atual, media(LPA dos ultimos 3-5 anos)); sem 3 anos de historico, fica so o LPA atual
- **Situação:** implementado
- **Contextos de uso:** Longo prazo

## Graham Number (segunda trava de COMPRA_FORTE)

Teto classico de Graham pro investidor defensivo: aceita, no maximo, P/L 15 e P/VP 1,5 ao mesmo tempo. Preco acima disso rebaixa COMPRA_FORTE pra COMPRA_MODERADA, mesmo com margem de seguranca alta.

- **Fórmula:** graham_number = sqrt(22,5 x LPA_normalizado x VPA)
- **Situação:** implementado
- **Contextos de uso:** Longo prazo

## Faixa neutra de venda

So e VENDA_VALUATION com margem de seguranca do cenario base abaixo de -15% - entre -15% e 0% a recomendacao e MANTER, nao venda. Antes, qualquer margem negativa virava venda.

- **Fórmula:** VENDA_VALUATION se margem_base < -15%; senao MANTER (dentro da faixa) ou outra regra de compra
- **Situação:** implementado
- **Contextos de uso:** Longo prazo

## Earnings yield e classificacao do P/L

O inverso do P/L, em %. Quanto maior, mais a empresa "paga" pelo preco pago pela acao.

- **Fórmula:** earnings yield = LPA_normalizado / preco; Atrativo >=12%, Razoavel >=8%, Baixo >=6%, senao Muito baixo
- **Situação:** implementado
- **Contextos de uso:** Longo prazo
