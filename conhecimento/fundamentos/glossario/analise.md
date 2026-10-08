---
tipo: fundamentos
colecao: glossario
titulo: Como se analisa
origem: painel-ativos-frontend/public/js/pages/GlossarioPage.js
disponivel_ate: 2000-01-01
gerado_em: 2026-10-08
hash: a6dbcfacfc26200fb86bc784ece45b508fde3dd6704c34faf1a84381afa20451
---

## Resumo

Os metodos e as contas que o sistema aplica.

## Analise fundamentalista

Olha o negocio - lucro, divida, crescimento - e pergunta se a empresa vale o preco.

- **Onde aparece no painel:** E o que os dados da CVM alimentam.

## Analise tecnica

Olha so o grafico de preco e volume, e pergunta para onde o preco esta indo.

- **Onde aparece no painel:** E o que o sinal tecnico da aba Como funciona faz.

## Valuation

O exercicio de estimar quanto a empresa deveria valer.

## Formula de Graham

Um calculo de preco justo criado por Benjamin Graham. A versao original (1962): preco justo = LPA x (8,5 + 2 x crescimento). A versao revisada (1974) multiplica isso por 4,4 / Y, onde Y e o rendimento de um titulo de referencia - sem esse ajuste, com juros de dois digitos como no Brasil, o preco justo sai inflado.

- **Onde aparece no painel:** Usamos a versao ajustada: Y = Selic meta vigente. Tres cenarios de crescimento (0%, 3%, 5%). A versao sem ajuste (fator 1) continua calculada, mas so como referencia historica - nao decide a recomendacao.

## Y (taxa livre de risco no Graham ajustado)

O rendimento de referencia que divide o fator 4,4 na formula revisada de Graham. Quanto maior Y, menor o preco justo calculado - juros altos exigem desconto maior pra compensar o custo de oportunidade de nao deixar o dinheiro rendendo sem risco.

- **Onde aparece no painel:** Selic meta vigente no dia da analise (indice_macro, codigo SELIC). Sem Selic disponivel no cache, o insight sai SEM_DADOS em vez de usar a formula sem ajuste escondida.

## Graham Number

Teto classico de Graham pro "investidor defensivo": raiz quadrada de 22,5 x LPA x VPA. Equivale a aceitar, no maximo, P/L 15 combinado com P/VP 1,5 ao mesmo tempo - nao usa juros, e um criterio patrimonial separado do preco justo.

- **Onde aparece no painel:** Segunda trava de COMPRA_FORTE: mesmo com margem de seguranca e earnings yield altos, se o preco passa do Graham Number (barato pelo lucro, caro pelo patrimonio), a recomendacao e rebaixada pra COMPRA_MODERADA.

## LPA normalizado

Em vez do lucro por acao de um unico exercicio (que pode estar no pico de um ciclo), usa-se o menor valor entre o LPA atual e a media dos ultimos 3 a 5 anos entregues a CVM.

- **Onde aparece no painel:** Evita que uma empresa ciclica (banco, commodity) pareca "barata" so porque o lucro do ano esta anormalmente alto.

## Lucro ciclico (ciclica no pico)

Empresa ciclica (banco, commodity) no pico do ciclo tem o LPA do ano bem acima da media historica; usar esse LPA sozinho faria a formula de Graham calcular um preco justo inflado e sair COMPRA_FORTE, mesmo com o lucro perto de cair. O LPA normalizado corrige isso antes do calculo (ver "LPA normalizado").

- **Onde aparece no painel:** Testado fixando o modo G_REAL (tests/test_valuation_selic_e_ciclo.py): esse modo nao depende do IPCA do dia, entao a proporcao entre LPA normalizado e preco justo sai exata; em G_NOMINAL/Y_REAL o resultado varia com o IPCA e nao daria um numero fixo pro teste.

## Referencia sem juros (cenario)

Segundo calculo de preco justo pela formula de Graham, feito com a taxa fixa historica (Y = 4,4%, fator 1) em vez da Selic do dia, e sempre no modo G_REAL - nao depende do IPCA, por isso nunca fica sem dado. Fica ao lado do cenario oficial so como referencia historica: nao entra na recomendacao nem na margem de seguranca de COMPRA/VENDA.

- **Onde aparece no painel:** Calculado em paralelo ao valuation oficial (ValuationAnalyzer.analyze, campo "referencia"). Usa G_REAL mesmo quando o cenario oficial usa outro modo - hoje G_NOMINAL, escolhido no DEC-08/TASK-54.

## Faixa neutra (de venda)

Intervalo de margem de seguranca negativa que ainda nao justifica VENDA_VALUATION - hoje, entre -15% e 0%. Abaixo disso e venda; dentro da faixa, o sistema classifica como MANTER.

- **Onde aparece no painel:** Sem faixa neutra, qualquer margem negativa virava "venda" e quase toda empresa de crescimento saia como venda, mesmo sendo so um pouco cara.

## Versao da regra

Identificador (formato AAAA.MM.DD-N) que muda toda vez que um limiar ou formula da recomendacao muda para a mesma entrada. Existe pra sinais de regras diferentes nunca caırem no mesmo placar de acerto.

- **Onde aparece no painel:** Gravado em todo insight e no diario de sinais. Comparar regras (v1 vs. v2) so faz sentido separando por essa versao.

## Point-in-time (data de entrega)

Usar, numa simulacao do passado, so a informacao que ja era publica naquela data - nao o balanco "do periodo", mas a data em que ele de fato foi entregue e ficou disponivel pro mercado (a CVM chama isso de DT_RECEB).

- **Onde aparece no painel:** Sem isso, o backtest usaria lucro que ninguem conhecia na epoca (look-ahead bias) - o balanco de um exercicio pode demorar meses para ser publicado.

## Universo amplo (backtest)

O conjunto de ativos testado no backtest, ampliado pra incluir empresas que ja saíram da bolsa (deslistadas) - nao so as monitoradas hoje. Testar so quem sobreviveu ate agora infla artificialmente o resultado (vies de sobrevivencia): empresa que quebrou nunca aparece como "erro" da regra.

- **Onde aparece no painel:** Em uso desde 27/09/2026 (TASK-59/51): o universo de cada ano sai do COTAHIST - ativos com pelo menos 200 pregões e volume médio de R$ 5 milhões por dia no ano anterior, sem units nem BDRs, incluindo quem saiu da bolsa. O último backtest cobriu 258 ativos.

## Placar segmentado

Separar, no resultado do backtest, as janelas que tiveram um ajuste aplicado (ex.: provento somado ao retorno) das que nao tiveram - em vez de misturar as duas no mesmo numero sem dizer quantas de cada.

- **Onde aparece no painel:** Proventos (ISS-F7/infra#TASK-36 e TASK-56): o retorno soma provento quando há dado, e o placar da aba Avaliação mostra quantas janelas de cada linha tiveram provento.

## Margem de seguranca

Quanto o preco justo esta acima do preco de mercado, em %. Positiva sugere desconto; negativa, que esta caro. Graham defendia so comprar com margem folgada, porque a conta pode estar errada.

## OHLCV / candle

Os cinco numeros de um dia de pregao: abertura, maxima, minima, fechamento e volume.

- **Onde aparece no painel:** Cada barra do grafico da aba Candles.

## Volume

Quantidade negociada. Volume alto da mais confianca ao movimento de preco.

## Media movel

A media do preco dos ultimos N dias, que se atualiza a cada dia. Suaviza o ruido e mostra a tendencia.

## Z-score

Quantos "desvios normais" o preco de hoje esta longe da media. Perto de 0 e normal; acima de 2, anormalmente esticado.

## Momentum

A estrategia que aposta na continuacao: se esta subindo, tende a continuar.

## Reversao a media

A aposta oposta: o que esticou demais tende a voltar.

## Maxima e minima de 52 semanas

O maior e o menor preco do ultimo ano. Serve de regua pra saber onde o preco esta hoje.
