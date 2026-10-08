---
tipo: fundamentos
colecao: glossario
titulo: Risco e resultado de uma operação
origem: painel-ativos-frontend/public/js/pages/GlossarioPage.js
disponivel_ate: 2000-01-01
gerado_em: 2026-10-08
hash: 04192f26cac287ae4cf1c5c1a263d23369014c367aba53e86ac55d065ff9fa83
---

## Resumo

Como medir se uma regra ou operação valeu a pena, e como limitar o estrago quando a hipótese estiver errada.

## Stop (ordem de proteção)

Ordem que encerra a posição se o preço atingir um nível definido antes da entrada, para limitar a perda quando a hipótese se mostra errada.

- **Cuidado:** Stop não garante preço: numa abertura com gap a ordem executa no primeiro preço disponível, que pode estar bem abaixo do planejado.
- **Onde aparece no painel:** O backtest do sistema não simula stop: mede o retorno do sinal em horizontes fixos de 21, 63 e 126 pregões.

## Relação retorno/risco

Quanto se espera ganhar para cada real arriscado. Risco de R$ 2 por ação (entrada até o stop) e alvo de R$ 4 dão 2:1, antes de custos.

- **Cuidado:** Uma razão atraente não compensa sozinha uma taxa de acerto baixa: 2:1 acertando 30% das vezes perde dinheiro.

## Payoff

Ganho médio das operações vencedoras dividido pela perda média das perdedoras. Junto com a taxa de acerto, define a expectativa da estratégia.

- **Exemplo:** Payoff 1,5 com 45% de acerto: 0,45 × 1,5 − 0,55 × 1 = +0,125 por unidade arriscada, antes de custos.
- **Cuidado:** Taxa de acerto isolada não diz nada; payoff isolado também não.

## Retorno simples e anualizado

Retorno simples = preço final ÷ preço inicial − 1. Anualizado converte para uma base de um ano, para comparar horizontes diferentes: (1 + retorno) ^ (252 ÷ pregões) − 1.

- **Exemplo:** +2% em 63 pregões equivale a cerca de +8,2% ao ano.
- **Cuidado:** Anualizar um período curto e bom extrapola sorte.
- **Onde aparece no painel:** O placar do backtest mostra o retorno médio por horizonte (21, 63, 126 pregões), com custo de 0,10% ida e volta e proventos quando há dado.

## Índice de Sharpe

Retorno acima da taxa livre de risco dividido pela volatilidade desse retorno. Mede retorno por unidade de oscilação: quanto maior, melhor a recompensa pelo risco corrido.

- **Cuidado:** Supõe que volatilidade é todo o risco - ignora caudas gordas e sequências de perdas. Compare Sharpe só entre períodos e universos iguais.
- **Onde aparece no painel:** Não é calculado; o placar compara com o CDI e com a carteira pelo excesso médio e seu intervalo de confiança.

## Buy-and-hold

Comprar e manter, sem operar. É a referência mínima de qualquer estratégia: se a regra não bate simplesmente segurar o mesmo universo no mesmo período, os sinais não agregaram nada.

- **Onde aparece no painel:** A "carteira" do placar do backtest é essa referência: a média de todos os ativos do universo em cada janela.

## Turnover

Quanto da carteira é trocado por período. Turnover alto multiplica custos de corretagem, emolumentos, spread e impostos.

- **Cuidado:** Uma estratégia com resultado bruto bom pode virar prejuízo líquido só pelo giro.

## Ordem a mercado e ordem limitada

A mercado executa já, no melhor preço disponível. Limitada só executa no preço definido ou melhor - pode não executar.

- **Cuidado:** A mercado troca certeza de execução por risco de preço (slippage); limitada troca certeza de preço por risco de ficar de fora.

## Custos de negociação

Corretagem, emolumentos e taxa de liquidação da B3, spread, slippage e imposto sobre o ganho. Somados, podem consumir todo o resultado de uma estratégia de giro alto.

- **Onde aparece no painel:** O backtest desconta 0,10% por operação (ida e volta); impostos não entram.

## Diário de operações

Registro feito ANTES do resultado: ativo, data e prazo; contexto do prazo maior; hipótese; gatilho objetivo; risco planejado e cenário de gap. Depois, o resultado líquido e se o plano foi seguido.

- **Cuidado:** Regra alterada depois de ver o desfecho não testa nada.
- **Onde aparece no painel:** O Diário de sinais da aba Avaliação é a versão automática: grava o sinal de cada regra no pregão em que foi dado e só depois mede o resultado.
