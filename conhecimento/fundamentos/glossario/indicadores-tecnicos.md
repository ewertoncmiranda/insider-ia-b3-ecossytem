---
tipo: fundamentos
colecao: glossario
titulo: Indicadores técnicos
origem: painel-ativos-frontend/public/js/pages/GlossarioPage.js
disponivel_ate: 2000-01-01
gerado_em: 2026-10-08
hash: 58f15de31cb8cade35882e34d59d9bee67f9973b3e43327ea0004c8241d1c419
---

## Resumo

Transformações do preço e do volume. Todos olham para trás e atrasam em relação ao movimento - e vários são versões do mesmo dado, não evidências independentes.

## SMA e EMA (média simples e exponencial)

A SMA dá o mesmo peso aos N últimos fechamentos. A EMA dá mais peso aos recentes: EMA de hoje = α × preço + (1 − α) × EMA de ontem, com α = 2 / (N + 1). A EMA reage mais rápido e erra mais em mercado lateral.

- **Sigla:** Simple / Exponential Moving Average
- **Exemplo:** SMA20 é a média dos últimos 20 fechamentos. Médias de 50 e 200 períodos são referências comuns, não leis.
- **Cuidado:** Cruzamento de médias costuma chegar tarde depois de um movimento forte. Preço acima de média subindo sugere regime de alta, não garante continuação.
- **Onde aparece no painel:** O sistema usa a SMA de 20 pregões (média móvel da ficha e base do z-score). EMA não é calculada.

## Sobrecompra e sobrevenda

Faixas convencionais do RSI (IFR): acima de 70 chama-se sobrecompra; abaixo de 30, sobrevenda. A linha de 50 separa predomínio recente de ganhos (acima) e de perdas (abaixo). A configuração clássica de Wilder usa 14 períodos.

- **Cuidado:** Não são ordens de venda ou compra: em tendência forte o RSI fica semanas acima de 70 enquanto o preço segue subindo.
- **Onde aparece no painel:** O RSI não é calculado pelo sistema; o z-score da ficha cumpre papel parecido (preço esticado em relação à média).

## Divergência

Preço e indicador contam histórias diferentes. De baixa: o preço faz topo mais alto e o RSI (ou MACD) faz topo mais baixo - o momentum está perdendo força. De alta: o preço faz fundo mais baixo e o indicador, fundo mais alto.

- **Exemplo:** Novo topo em R$ 42 com o RSI abaixo do topo anterior.
- **Cuidado:** Divergências podem durar muito antes de qualquer reversão. Compare pivôs equivalentes e confirme com perda de estrutura, não com a divergência sozinha.

## Histograma do MACD

Barras com a diferença entre a linha MACD (EMA12 − EMA26) e a linha de sinal (EMA9 do MACD). Barras crescendo mostram momentum acelerando; encolhendo, desacelerando.

- **Cuidado:** Histograma positivo não garante alta futura, e em mercado lateral o MACD cruza o sinal o tempo todo.
- **Onde aparece no painel:** O MACD não é calculado pelo sistema.

## Volatilidade

O quanto o preço oscila, independentemente da direção. Um ativo pode subir e ainda assim oscilar o bastante para acionar o stop de uma operação mal dimensionada.

- **Cuidado:** Direção e risco são perguntas diferentes: indicador de volatilidade não diz se o preço vai subir ou cair.
- **Onde aparece no painel:** A amplitude intradiária e o desvio-padrão por trás do z-score são as medidas de oscilação que o sistema calcula.

## True Range e ATR

True Range é o maior entre: máxima − mínima do dia; |máxima − fechamento anterior|; |mínima − fechamento anterior| - ou seja, a amplitude contando o gap. ATR é a média suavizada do True Range, em geral de 14 períodos (Wilder).

- **Sigla:** Average True Range
- **Exemplo:** ATR14 de R$ 1,20 significa que o papel oscila, em média, R$ 1,20 por pregão. Um stop a 2 ATR ficaria R$ 2,40 abaixo da entrada.
- **Cuidado:** Stop baseado em ATR se adapta à volatilidade, mas não elimina perdas nem garante o preço de execução.
- **Onde aparece no painel:** O ATR não é calculado pelo sistema, mas as velas do banco (máxima, mínima e fechamento desde 2016) permitem calculá-lo.

## VWAP

Preço médio do período ponderado pelo volume negociado em cada preço. Muito usado dentro do dia como referência de execução de ordens grandes.

- **Sigla:** Volume Weighted Average Price
- **Cuidado:** VWAP do dia não é preço justo fundamental - é só o preço médio pelo qual o mercado negociou.
- **Onde aparece no painel:** Exige dados intradiários, que o sistema não tem.

## OBV

Volume acumulado: soma o volume dos dias de alta e subtrai o dos dias de baixa. Usado para ver se o volume acompanha o preço ou diverge dele.

- **Sigla:** On-Balance Volume
- **Cuidado:** Um dia de volume extraordinário (rebalanceamento de índice, leilão) distorce a série inteira dali para frente.

## Volume x número de negócios

Volume é a quantidade (ou valor) negociada; número de negócios é quantas operações aconteceram. Um único negócio grande pode gerar volume alto com poucos participantes.

- **Cuidado:** Volume alto de poucos negócios confirma menos um movimento que o mesmo volume espalhado em muitos.
- **Onde aparece no painel:** O COTAHIST traz os dois; o sistema usa o volume (score de volume da análise técnica e filtro de liquidez do backtest).

## Liquidez de negociação

Facilidade de comprar ou vender sem mover o preço: volume diário, spread entre compra e venda e profundidade do livro de ofertas. Diferente da liquidez corrente, que é um indicador contábil.

- **Cuidado:** Uma estratégia que funciona no papel pode ser inexecutável em ativo pouco líquido - a própria ordem move o preço.
- **Onde aparece no painel:** O universo do backtest exige volume médio de pelo menos R$ 5 milhões por dia no ano anterior; a aba Velas marca pregões de liquidez baixa.
