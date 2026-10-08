---
tipo: fundamentos
colecao: glossario
titulo: Decisões fundamentadas do ecossistema
origem: painel-ativos-frontend/public/js/pages/GlossarioPage.js
disponivel_ate: 2000-01-01
gerado_em: 2026-10-08
hash: c697dd145cbf0373e53abbbd626ab9c26f13193cf580c32a3ba4b36c88b0c23d
---

## Resumo

Como o sistema transforma preço, balanço, juros e histórico em leitura de negócio.

## Decisão consolidada

A leitura final que o backend Java monta a partir de várias análises já gravadas. Ela combina o sinal predominante, a margem de segurança média, a família da recomendação e a quantidade de registros disponíveis.

- **Cuidado:** Mais registros aumentam a confiança operacional, mas não provam acerto futuro. O acerto é medido separadamente no diário e no backtest.
- **Onde aparece no painel:** Aparece em Gestão e na tabela única de Ativos. Não é cálculo novo de valuation; é consolidação dos resultados produzidos pelo gerar-insights.

## Sinal quantitativo

Classificação produzida por regra matemática sobre dados de mercado ou fundamentos. Pode ser positivo, neutro, negativo ou sem dados, mas não é uma ordem de compra ou venda.

- **Cuidado:** No Brasil, recomendar investimento é atividade regulada. Por isso o painel deve tratar o sinal como leitura automática, não como recomendação profissional.
- **Onde aparece no painel:** Vem do gerar-insights, é lido pelo gestor e exibido no front com aviso de regra experimental.

## Margem de segurança

Distância entre o preço de mercado e o preço justo estimado. Se o valor justo é 100 e o preço é 70, a margem é 30%.

- **Cuidado:** Margem alta pode indicar oportunidade ou problema escondido no balanço. Ela depende da qualidade do LPA, da taxa de juros e do setor.
- **Onde aparece no painel:** Calculada pelo gerar-insights com os cenários de Graham e usada pelo gestor para risco e decisão consolidada.

## Preço justo de Graham ajustado por juros

Estimativa de valor que parte do LPA e de uma taxa de crescimento, depois ajusta pelo nível de juros. Juros mais altos reduzem o preço justo aceitável.

- **Onde aparece no painel:** Calculado no gerar-insights usando Selic como referência de juros e gravado no payload de fundamentos.
- **Referência:** Benjamin Graham; ajuste 4,4 / Y, com Y representado no sistema pela Selic vigente.

## LPA normalizado

Lucro por ação suavizado com histórico de 3 a 5 anos para reduzir o efeito de um ano excepcionalmente bom ou ruim.

- **Cuidado:** Empresas cíclicas podem parecer baratas no pico do lucro. Normalizar o LPA reduz esse viés.
- **Onde aparece no painel:** Usado pelo gerar-insights antes do valuation, quando a base CVM oferece histórico suficiente.

## Graham Number

Trava complementar de valor que combina LPA e VPA. Ajuda a evitar que uma ação pareça barata só pelo lucro, mas esteja cara em relação ao patrimônio.

- **Onde aparece no painel:** Calculado pelo gerar-insights quando há VPA válido vindo da CVM.

## Momentum

Leitura de continuação de tendência: preço acima da média móvel com volume relativo forte sugere força compradora; abaixo da média com volume fraco sugere perda de força.

- **Cuidado:** Momentum não substitui fundamento. O projeto mede esse sinal separado do valuation para não misturar hipóteses antes de provar acerto.
- **Onde aparece no painel:** Calculado sobre a série histórica como sinal técnico e medido no backtest como regra própria.

## Reversão à média

Hipótese de que preços muito afastados da média tendem a voltar para perto dela. O sistema observa z-score e proximidade de mínimas ou máximas de 52 semanas.

- **Cuidado:** Preço barato pode continuar barato se o fundamento piorou. A reversão só faz sentido quando o desvio não é explicado por mudança real do negócio.
- **Onde aparece no painel:** Calculada pelo gerar-insights e registrada como regra técnica própria no backtest.

## Taxa-base

A proporção de janelas que subiram ou caíram no mesmo período, independentemente da regra. Serve para saber se a regra venceu o ambiente geral ou só surfou o mercado.

- **Exemplo:** Se 60% das ações subiram em 63 pregões, uma regra de compra com 58% de acerto não agregou valor.
- **Onde aparece no painel:** Mostrada no backtest e no diário de sinais.

## Intervalo de confiança

Faixa estatística que mostra a incerteza da estimativa. Se o intervalo cruza a taxa-base, o resultado ainda é inconclusivo.

- **Onde aparece no painel:** Usado no placar de backtest, ranking e diário para evitar promover regra por ruído.

## Retorno total

Retorno que soma a variação do preço e os proventos recebidos no período. É mais fiel que olhar só o preço, especialmente para bancos, elétricas e empresas pagadoras de dividendos.

- **Onde aparece no painel:** Backtest e diário somam proventos B3/CVM quando disponíveis.

## Viés de futuro

Erro de teste em que a regra usa informação que ainda não existia no momento da decisão. Faz uma estratégia parecer melhor do que seria na vida real.

- **Onde aparece no painel:** O backtest evita isso entrando na abertura do pregão seguinte ao sinal e usando apenas balanços já entregues à CVM na data.

## Ponto no tempo

Princípio de usar somente os dados conhecidos naquela data histórica. Um balanço entregue depois não pode influenciar uma decisão passada.

- **Onde aparece no painel:** Base dos fundamentos no backtest e dos fatores mensais.

## Cobertura da métrica

Explicação de por que um indicador existe ou está nulo. Nulo pode ser ausência de dado, regra setorial ou conta incompatível.

- **Onde aparece no painel:** Vem do ETL CVM em `cobertura_json` e ajuda o front a não confundir nulo com zero.

## Base de fundamentos

Conjunto de demonstrações CVM transformadas em indicadores como ROE, ROIC, margem, dívida líquida, LPA, VPA e fluxo de caixa.

- **Onde aparece no painel:** Produzida pelo etl-fundamentos-cvm nas tabelas `fato_contabil` e `indicador_fundamentalista`.
- **Referência:** DFP, ITR, FCA, FRE, DRE, balanço patrimonial, DFC e DVA.

## Provento contábil x provento de evento

Provento contábil vem da DVA/DFP/ITR e representa dividendos e JCP declarados no período. Provento de evento vem da B3 e traz data-com e pagamento aprovados.

- **Cuidado:** A B3 pública costuma cobrir só uma janela recente; a CVM cobre histórico, mas nem sempre tem a data exata do evento.
- **Onde aparece no painel:** O backtest combina as duas fontes para estimar retorno total histórico sem dupla contagem.
