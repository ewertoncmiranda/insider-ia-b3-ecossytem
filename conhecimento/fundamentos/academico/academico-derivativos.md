---
tipo: fundamentos
colecao: academico
titulo: "Derivativos, câmbio e divulgação"
origem: painel-ativos-frontend/public/js/estudos/glossarioAcademico.js
disponivel_ate: 2000-01-01
gerado_em: 2026-10-08
hash: a033ba842d22008e56d83a420227bbae2e92c75e0c0fb389f033392bf0025840
---

## Resumo

Contratos, sensibilidades e informações contábeis.

## Ativo subjacente

Ativo, taxa, índice ou variável de que depende o valor do derivativo.

- **Exemplo:** O dólar é subjacente de um futuro cambial.
- **Cuidado:** O derivativo pode ter riscos adicionais aos movimentos do subjacente.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Contrato a termo — forward

Acordo bilateral para comprar ou vender no futuro por condições definidas hoje.

- **Exemplo:** Empresa fixa uma taxa cambial para recebimento futuro.
- **Cuidado:** Há risco de contraparte e menor padronização que contratos de bolsa.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Contrato futuro

Contrato padronizado negociado em mercado organizado, normalmente sujeito a margem e ajuste diário.

- **Exemplo:** Futuro de DI reflete negociação de taxa para um vencimento.
- **Cuidado:** Alavancagem e ajustes podem exigir caixa antes do vencimento.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Swap

Contrato de troca de resultados financeiros calculados sobre referenciais definidos.

- **Exemplo:** Trocar variação cambial por taxa de juros.
- **Cuidado:** A proteção pode gerar risco de base, crédito e liquidez.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Opção, prêmio e preço de exercício

Opção confere um direito ao comprador; prêmio é seu preço e exercício é o valor contratual para comprar ou vender o subjacente.

- **Exemplo:** Uma call pode dar direito de compra a preço determinado.
- **Cuidado:** O comprador pode perder todo o prêmio; o vendedor pode assumir perda elevada.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Call — opção de compra

Direito de comprar o ativo subjacente por preço de exercício definido até ou no vencimento, conforme o estilo da opção.

- **Exemplo:** Compra de call busca exposição positiva à alta do ativo, limitada ao prêmio pago pelo titular.
- **Cuidado:** Não use como sinônimo de compra garantida de lucro; prêmio pode virar perda total.
- **Onde aparece no painel:** Base conceitual para estudar séries de opções da B3 e relacioná-las às cotações do ativo-objeto no módulo de estudos.

## Put — opção de venda

Direito de vender o ativo subjacente por preço de exercício definido até ou no vencimento, conforme o estilo da opção.

- **Exemplo:** Compra de put pode proteger uma carteira contra queda do ativo.
- **Cuidado:** Não confundir proteção parcial com eliminação total de risco; prêmio, prazo e liquidez importam.
- **Onde aparece no painel:** Serve para relacionar proteção, cenário de baixa e payoff no laboratório de opções.

## Titular da opção

Comprador da opção, que paga o prêmio e possui o direito previsto no contrato.

- **Exemplo:** Titular de uma call decide se exercerá o direito de comprar nas condições do contrato.
- **Cuidado:** Ter o direito não obriga exercício nem garante ganho líquido.
- **Onde aparece no painel:** Usado no glossário e nas fichas de payoff para separar direito do comprador e obrigação do vendedor.

## Lançador da opção

Vendedor da opção, que recebe o prêmio e assume obrigação se o titular exercer.

- **Exemplo:** Lançador de call pode ter de entregar o ativo se a opção for exercida.
- **Cuidado:** Venda descoberta pode ter perda elevada ou teoricamente ilimitada; exige margem e controle externo ao painel.
- **Onde aparece no painel:** No sistema, deve aparecer como alerta de risco antes de qualquer simulação operacional.

## Prêmio

Preço pago pelo titular e recebido pelo lançador para negociar a opção.

- **Exemplo:** Uma opção cotada a R$ 0,80 por ação custa R$ 80 se o contrato representar 100 ações.
- **Cuidado:** Prêmio baixo não significa oportunidade; pode refletir baixa probabilidade, pouco prazo ou baixa liquidez.
- **Onde aparece no painel:** É insumo para custo inicial, breakeven e perda máxima nas fichas de estratégia.

## Strike — preço de exercício

Preço contratual pelo qual o ativo pode ser comprado ou vendido no exercício da opção.

- **Exemplo:** Call com strike 25 dá direito de comprar a R$ 25, observadas as regras da série.
- **Cuidado:** Comparar strikes sem vencimento, tipo e prêmio produz análise incompleta.
- **Onde aparece no painel:** Deve ser cruzado com ativo-objeto, vencimento e prêmio nas séries da B3.

## Vencimento da opção

Data em que a opção expira ou em que se avalia seu exercício, conforme regras aplicáveis.

- **Exemplo:** Uma estratégia montada perto do vencimento tem pouco tempo para o cenário ocorrer.
- **Cuidado:** Vencimento curto aumenta sensibilidade ao tempo e pode invalidar backtests simplificados.
- **Onde aparece no painel:** É filtro obrigatório em qualquer ranking de estratégias de opções.

## Estilo americano e europeu

Estilo americano permite exercício até o vencimento; estilo europeu restringe o exercício ao vencimento.

- **Exemplo:** Duas opções com mesmo ativo e strike podem ter regras de exercício diferentes.
- **Cuidado:** Não presuma exercício livre sem verificar a especificação da série.
- **Onde aparece no painel:** Aparece como metadado para explicar limitações de payoff e risco antes do vencimento.

## Moneyness — ITM, ATM e OTM

Classificação da posição do strike em relação ao preço do ativo: dentro, no dinheiro ou fora do dinheiro.

- **Exemplo:** Uma call está ITM quando o ativo está acima do strike; uma put está ITM quando o ativo está abaixo do strike.
- **Cuidado:** A classificação muda com o preço e não informa sozinha se a opção está barata ou cara.
- **Onde aparece no painel:** Ajuda a organizar cadeias por distância do strike e cenário de mercado.

## Payoff

Resultado bruto de uma opção ou estratégia em função do preço do ativo, especialmente no vencimento.

- **Exemplo:** Compra de call tem payoff zero abaixo do strike e cresce acima dele, antes de descontar o prêmio.
- **Cuidado:** Payoff no vencimento não captura variação de volatilidade, liquidez e fechamento antecipado.
- **Onde aparece no painel:** Base para as fichas didáticas e para simulações futuras de estratégias.

## Breakeven — ponto de equilíbrio

Preço do ativo em que o resultado líquido da estratégia é aproximadamente zero, dadas as premissas.

- **Exemplo:** Call comprada: strike + prêmio por ação, sem considerar custos adicionais.
- **Cuidado:** Custos, taxas, spread e exercício podem deslocar o ponto de equilíbrio.
- **Onde aparece no painel:** Usado para comparar cenário exigido pela estratégia com volatilidade histórica e tendência.

## Perda máxima

Maior perda estimada de uma posição sob as regras definidas, considerando payoff e custos informados.

- **Exemplo:** Compra de opção tem perda limitada ao prêmio e custos; venda descoberta pode não ter limite prático simples.
- **Cuidado:** A estimativa é inválida se ignorar margem, exercício antecipado, liquidez ou gaps.
- **Onde aparece no painel:** Deve ser campo obrigatório antes de exibir assertividade de opções.

## Ganho máximo

Maior ganho estimado de uma estratégia sob as regras definidas.

- **Exemplo:** Trava de alta com call tem ganho máximo limitado pela distância entre strikes menos o débito.
- **Cuidado:** Ganho máximo alto pode ter baixa probabilidade ou depender de liquidez inexistente.
- **Onde aparece no painel:** Ajuda a comparar retorno por unidade de risco nas estratégias do playbook.

## Trava de alta com call — bull call spread

Estratégia direcional de alta montada com compra de call em strike menor e venda de call em strike maior, mesmo vencimento.

- **Exemplo:** Aposta em alta moderada com custo menor que a compra seca de call.
- **Cuidado:** Limita ganhos; não deve ser usada quando o cenário exige explosão acima do strike vendido.
- **Onde aparece no painel:** Relaciona cenário de alta, tendência, volatilidade e custo inicial no laboratório.

## Trava de baixa com put — bear put spread

Estratégia direcional de baixa montada com compra de put em strike maior e venda de put em strike menor, mesmo vencimento.

- **Exemplo:** Busca ganho em queda moderada com risco limitado ao débito líquido.
- **Cuidado:** Não captura quedas muito fortes além do ganho máximo da trava.
- **Onde aparece no painel:** Relaciona cenário de baixa, suporte rompido e custo de proteção no estudo.

## Lançamento coberto — covered call

Venda de call contra uma posição comprada no ativo subjacente.

- **Exemplo:** Investidor com ações vende call para receber prêmio e aceita limitar parte da alta.
- **Cuidado:** Não protege plenamente contra queda do ativo e pode obrigar entrega da ação.
- **Onde aparece no painel:** Só faz sentido no sistema quando a carteira/posição no ativo for conhecida ou simulada explicitamente.

## Venda de put coberta por caixa — cash-secured put

Venda de put mantendo caixa suficiente para comprar o ativo se exercido.

- **Exemplo:** Recebe prêmio assumindo a obrigação potencial de comprar o ativo no strike.
- **Cuidado:** Não usar sem caixa, sem limite de posição ou em ativo que não se aceitaria comprar.
- **Onde aparece no painel:** Pode virar cenário didático de entrada planejada, mas não deve ser recomendação automática.

## Straddle

Compra simultânea de call e put no mesmo strike e vencimento, ou venda simultânea das duas pernas.

- **Exemplo:** Straddle comprado busca movimento forte em qualquer direção.
- **Cuidado:** Pode perder com lateralização e queda de volatilidade; straddle vendido tem risco elevado.
- **Onde aparece no painel:** Útil para estudar explosão de volatilidade, eventos e limites de dados de volatilidade implícita.

## Strangle

Estratégia com call e put de strikes diferentes no mesmo vencimento, geralmente fora do dinheiro.

- **Exemplo:** Strangle comprado costuma ser mais barato que straddle, mas exige movimento maior.
- **Cuidado:** Não usar apenas porque o prêmio é menor; breakevens ficam mais distantes.
- **Onde aparece no painel:** Relaciona volatilidade, amplitude histórica e eventos no laboratório de cenários.

## Borboleta — butterfly

Combinação de opções com três strikes para buscar resultado máximo perto do strike central.

- **Exemplo:** Uma borboleta com calls pode comprar uma call baixa, vender duas calls centrais e comprar uma call alta.
- **Cuidado:** Estratégia sensível a custos e precisão do preço-alvo; ruim em spreads largos.
- **Onde aparece no painel:** Serve para estudar cenário de preço-alvo e liquidez de múltiplas pernas.

## Condor e iron condor

Estruturas de quatro pernas que buscam lucro em faixa de preços, com perda limitada quando bem montadas.

- **Exemplo:** Iron condor combina uma trava de put e uma trava de call para cenário lateral.
- **Cuidado:** Não usar quando há evento de alta volatilidade não modelado ou baixa liquidez nas pernas.
- **Onde aparece no painel:** Relaciona lateralização, bandas de preço e custo de execução de múltiplas pernas.

## Volatilidade histórica

Medida de variação realizada do preço do ativo em uma janela passada.

- **Exemplo:** Desvio-padrão anualizado dos retornos diários de 21 pregões.
- **Cuidado:** Passado não determina volatilidade futura; janela escolhida altera a leitura.
- **Onde aparece no painel:** Pode ser calculada com preços existentes para comparar cenários de opções.

## Volatilidade implícita

Volatilidade inferida do preço da opção por um modelo, dadas outras premissas.

- **Exemplo:** Prêmio maior pode implicar volatilidade implícita maior, mantidos os demais fatores.
- **Cuidado:** Sem modelo, taxa, dividendos e preço confiável, a estimativa pode enganar.
- **Onde aparece no painel:** Requer implementação específica; não deve ser presumida apenas com COTAHIST.

## Theta

Sensibilidade aproximada do preço da opção à passagem do tempo.

- **Exemplo:** Opções compradas tendem a perder valor com o tempo, mantido o restante.
- **Cuidado:** Theta não age sozinho; preço, volatilidade e juros também mudam.
- **Onde aparece no painel:** Importante para bloquear estratégias compradas perto do vencimento sem movimento esperado.

## Gamma

Sensibilidade do delta à mudança do preço do ativo subjacente.

- **Exemplo:** Gamma maior indica que o delta muda mais rapidamente quando o ativo se move.
- **Cuidado:** Pode aumentar perto do vencimento e tornar hedge instável.
- **Onde aparece no painel:** Conceito avançado; deve aparecer como alerta quando a plataforma evoluir para gregas.

## Rho

Sensibilidade aproximada do preço da opção à taxa de juros.

- **Exemplo:** Mudanças de juros podem afetar preço teórico de opções, especialmente prazos maiores.
- **Cuidado:** Em opções curtas, outros fatores podem dominar a variação.
- **Onde aparece no painel:** Termo de referência para futura precificação, não para ranking simples atual.

## Liquidez da opção

Capacidade de comprar ou vender a opção com volume e spread compatíveis com a estratégia.

- **Exemplo:** Série com negócios frequentes e spread estreito tende a ser mais executável.
- **Cuidado:** Último preço sem negócios recentes pode ser enganoso.
- **Onde aparece no painel:** Filtro obrigatório para evitar ranking de estratégias inviáveis.

## Probabilidade de lucro

Estimativa da frequência de cenários em que uma estratégia termina positiva, sob método definido.

- **Exemplo:** Backtest pode mostrar lucro em 55% das ocorrências de uma trava.
- **Cuidado:** Alta probabilidade com perdas grandes pode ser ruim; não substitui valor esperado.
- **Onde aparece no painel:** Deve ser exibida junto de payoff médio, perda máxima, custos e amostra.

## Profit factor

Soma dos ganhos dividida pela soma das perdas em um conjunto de operações.

- **Exemplo:** Ganhos totais de R$ 3.000 e perdas totais de R$ 2.000 resultam em 1,5.
- **Cuidado:** Pode ser instável com poucas operações ou perdas ainda não observadas.
- **Onde aparece no painel:** Métrica complementar no laboratório de assertividade, nunca isolada.

## Diário de opções — paper trading

Registro simulado de decisões, preços, regras e resultados antes de operar com dinheiro real.

- **Exemplo:** Anotar por que uma trava foi escolhida, qual era o cenário e quando seria encerrada.
- **Cuidado:** Simulação sem disciplina de preço e custos não reproduz execução real.
- **Onde aparece no painel:** Recomendado antes de liberar qualquer automação operacional no ecossistema.

## Delta

Sensibilidade aproximada do preço de uma opção a pequena mudança no subjacente.

- **Exemplo:** Delta 0,50 sugere variação aproximada de 0,50 para mudança unitária no ativo.
- **Cuidado:** Delta muda com preço, tempo e volatilidade.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Vega

Sensibilidade do preço de uma opção à volatilidade implícita.

- **Exemplo:** Uma posição long vega tende a ganhar com aumento de volatilidade, mantido o restante.
- **Cuidado:** É uma aproximação local e interage com outras sensibilidades.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Cupom cambial

Taxa de juros em moeda nacional associada a operações referenciadas em moeda estrangeira, conforme convenções do mercado.

- **Exemplo:** A relação entre juros domésticos, câmbio à vista e futuro informa o cupom.
- **Cuidado:** Convenções, impostos, liquidez e risco de crédito afetam a comparação.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Risco de base

Risco de o instrumento de proteção não variar na mesma proporção da exposição protegida.

- **Exemplo:** Hedge com contrato semelhante, mas não idêntico, ao fluxo da empresa.
- **Cuidado:** Mesmo um hedge bem desenhado pode manter exposição residual.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Valor justo

Preço estimado para transferência de um ativo ou passivo em transação ordenada, conforme a norma aplicável.

- **Exemplo:** Derivativo pode ser remensurado a valor justo a cada balanço.
- **Cuidado:** Modelo, dados não observáveis e risco de crédito introduzem incerteza.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Hedge accounting

Tratamento contábil que busca alinhar efeitos do instrumento de proteção e do item protegido.

- **Exemplo:** Documentar relação de hedge e sua efetividade.
- **Cuidado:** Exige critérios formais; uso econômico de derivativo não basta para enquadramento.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Disclosure — evidenciação

Divulgação de informações relevantes para compreender posição, risco, método e resultado.

- **Exemplo:** Nota informa nocional, valor justo, vencimento e finalidade dos derivativos.
- **Cuidado:** Mais páginas não significam automaticamente maior qualidade informacional.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.
