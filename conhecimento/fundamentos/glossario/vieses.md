---
tipo: fundamentos
colecao: glossario
titulo: Vieses e armadilhas de analise
origem: painel-ativos-frontend/public/js/pages/GlossarioPage.js
disponivel_ate: 2000-01-01
gerado_em: 2026-10-08
hash: 4c518df66788d55d7e67fc4f81d51cb40537383ae0ecacac86d16d932b1ef833
---

## Resumo

Os erros de leitura que mais custam dinheiro. Cada um esta explicado em detalhe na aba Padroes e armadilhas.

## Apofenia

A tendencia do cerebro de enxergar padrao onde so ha ruido. Uma serie de precos aleatoria produz figuras graficas impecaveis.

- **Onde aparece no painel:** O maior risco de qualquer analise visual de grafico.

## Look-ahead bias

Avaliar uma decisao do passado ja sabendo o que aconteceu depois. No grafico historico o padrao e obvio porque ja terminou.

## Timeframe shopping

Trocar o periodo do grafico ate encontrar um que confirme a tese que voce ja tinha. Nao e analise, e busca por concordancia.

## Ancoragem

Decidir com base no proprio preco de compra ("vendo quando voltar ao que paguei"). O mercado nao sabe quanto voce pagou.

## Caudas gordas

Retornos de acoes produzem eventos extremos com muito mais frequencia do que a distribuicao normal preve.

- **Onde aparece no painel:** Por isso um z-score de 3 aqui nao e tao raro quanto a estatistica classica sugeriria.

## Preco ajustado

Serie corrigida por dividendos e desdobramentos. Sem o ajuste, o preco cai no dia ex sem ninguem ter vendido e parece queda de mercado.

- **Onde aparece no painel:** Coluna fechamento_ajustado; passou a alimentar o calculo tecnico em 26/09/2026.

## Spread

Diferenca entre a melhor oferta de compra e a de venda. Em ativo pouco liquido, o spread pode consumir o movimento inteiro que o grafico mostra.

## Escala logaritmica

Escala em que a mesma variacao percentual ocupa a mesma altura. E a leitura correta para series longas; a linear exagera os valores altos.

## p-hacking

Testar muitos indicadores ate um parecer funcionar. Com 20 tentativas, achar algo "significativo" a 5% e o esperado, nao uma descoberta.
