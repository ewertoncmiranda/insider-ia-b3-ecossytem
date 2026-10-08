---
tipo: fundamentos
colecao: padroes
titulo: Padrões de velas
origem: painel-ativos-frontend/public/js/estudos/glossarioPadroes.js
disponivel_ate: 2000-01-01
gerado_em: 2026-10-08
hash: cc1d3b86e9be5613895c0b145f38f7f446232b71c0de110673e42ca13ab2c472
---

## Resumo

Padrões de velas reconhecidos pelo detector da aba Velas: o que cada desenho sugere, onde perde sentido e como o painel o detecta (regra mecânica, pode diferir do livro).

## Doji

- **Fundamento:** Abertura e fechamento praticamente iguais: compradores e vendedores empurraram o preço durante o pregão e terminaram empatados. O tamanho das sombras mostra quão longe cada lado chegou antes de recuar.
- **Indica:** Indecisão, não direção. Depois de uma tendência longa, sugere que o lado dominante perdeu força; no meio de um movimento lateral, não diz nada.
- **Cenários:** Topo ou fundo de uma tendência já estabelecida, como aviso de possível pausa.; Perto de suporte, resistência ou da máxima/mínima de 52 semanas.; Perde sentido em ativo de baixa liquidez, onde abertura e fechamento podem ser um único negócio.
- **Combina com:** estrela-manha; estrela-noite; harami; volume-anomalo
- **Neste painel:** Corpo de no máximo 10% da amplitude do dia. Aparece ~3,8 vezes por janela em séries aleatórias: sozinho, é comum demais para ser informação.

## Martelo

- **Fundamento:** O preço foi derrubado com força durante o pregão, mas os compradores absorveram a venda e levaram o fechamento de volta para perto da máxima. A sombra inferior longa é o registro dessa rejeição da baixa.
- **Indica:** Possível esgotamento da queda. É um sinal de alerta, não de compra: a confirmação clássica é o pregão seguinte fechar acima do corpo do martelo.
- **Cenários:** Somente depois de uma queda — a mesma forma depois de alta é o enforcado.; Mais relevante quando toca um suporte conhecido ou a mínima de 52 semanas.; Ganha peso com volume acima da média no dia do martelo ou na confirmação.
- **Combina com:** engolfo-alta; estrela-manha; volume-anomalo; doji
- **Neste painel:** Sombra inferior de pelo menos 2x o corpo, sombra superior no máximo do tamanho do corpo, e queda de 2% ou mais nas 5 velas anteriores.

## Enforcado

- **Fundamento:** Geometria idêntica à do martelo, mas no topo de uma alta. A sombra inferior longa mostra que, pela primeira vez em dias, houve venda forte o bastante para derrubar o preço durante o pregão.
- **Indica:** Primeiro sinal de que a alta pode estar perdendo sustentação. É mais fraco que o martelo: exige confirmação por fechamento abaixo do corpo no dia seguinte.
- **Cenários:** Somente depois de uma alta — é o contexto que separa o enforcado do martelo.; Mais relevante perto de resistência ou da máxima de 52 semanas.; Sem confirmação no pregão seguinte, costuma ser só ruído.
- **Combina com:** engolfo-baixa; estrela-noite; estrela-cadente; volume-anomalo
- **Neste painel:** Mesma regra geométrica do martelo, com alta de 2% ou mais nas 5 velas anteriores.

## Estrela cadente

- **Fundamento:** Os compradores levaram o preço bem acima da abertura, mas não conseguiram sustentar: o fechamento voltou para perto da mínima. A sombra superior longa registra a rejeição dos preços mais altos.
- **Indica:** Possível exaustão da alta. É o espelho do martelo: sinal de alerta que pede confirmação por queda no pregão seguinte.
- **Cenários:** Somente depois de uma alta — depois de queda, a mesma forma é chamada de martelo invertido.; Mais forte quando a sombra toca uma resistência ou a máxima de 52 semanas.; Ganha peso com volume alto, que mostra que muita gente vendeu naqueles preços.
- **Combina com:** estrela-noite; engolfo-baixa; enforcado; volume-anomalo
- **Neste painel:** Sombra superior de pelo menos 2x o corpo, sombra inferior no máximo do tamanho do corpo, e alta de 2% ou mais nas 5 velas anteriores.

## Marubozu de alta

- **Fundamento:** Corpo cheio, quase sem sombras: abriu perto da mínima e fechou perto da máxima. Os compradores controlaram o pregão do primeiro ao último negócio, sem recuo relevante.
- **Indica:** Força compradora naquele dia. No início de um movimento, sugere continuação; depois de uma alta longa, pode ser o último fôlego (clímax de compra).
- **Cenários:** Rompimento de uma resistência ou de uma faixa lateral.; Saída de um fundo, confirmando um martelo ou uma estrela da manhã.; Desconfie em dia de notícia ou de gap: o corpo cheio pode ser só a reação a um fato isolado.
- **Combina com:** martelo; estrela-manha; engolfo-alta; volume-anomalo
- **Neste painel:** Corpo de pelo menos 90% da amplitude, com fechamento acima da abertura.

## Marubozu de baixa

- **Fundamento:** Corpo cheio de baixa: abriu perto da máxima e fechou perto da mínima. Os vendedores dominaram a sessão inteira, sem que os compradores conseguissem reagir.
- **Indica:** Força vendedora naquele dia. No início de uma queda, sugere continuação; depois de uma queda longa, pode ser capitulação (venda em pânico perto do fundo).
- **Cenários:** Perda de um suporte ou saída de uma faixa lateral para baixo.; Confirmação de um enforcado, estrela cadente ou estrela da noite.; Confira se não é dia ex-dividendos com preço bruto: a queda pode ser só o provento saindo do preço.
- **Combina com:** estrela-noite; engolfo-baixa; enforcado; gap
- **Neste painel:** Corpo de pelo menos 90% da amplitude, com fechamento abaixo da abertura.

## Engolfo de alta

- **Fundamento:** Depois de um dia de baixa, o dia seguinte abre no nível do fechamento anterior (ou abaixo) e fecha acima da abertura anterior. Os compradores desfizeram toda a queda da véspera e ainda avançaram.
- **Indica:** Troca de controle de vendedores para compradores. Quanto maior o corpo da segunda vela em relação à primeira, mais forte a leitura.
- **Cenários:** Depois de uma queda — no meio de uma lateralização é extremamente comum e pouco informativo.; Perto de suporte ou da mínima de 52 semanas.; Com volume acima da média na segunda vela; sem volume, a troca de controle é duvidosa.
- **Combina com:** martelo; estrela-manha; marubozu-alta; volume-anomalo
- **Neste painel:** Vela anterior de baixa, atual de alta, abertura ≤ fechamento anterior e fechamento ≥ abertura anterior. Aparece ~7,4 vezes por janela no ruído: compare a contagem real com esse número.

## Engolfo de baixa

- **Fundamento:** Depois de um dia de alta, o dia seguinte abre no nível do fechamento anterior (ou acima) e fecha abaixo da abertura anterior. Os vendedores apagaram toda a alta da véspera.
- **Indica:** Troca de controle de compradores para vendedores. É um dos padrões de reversão de topo mais citados, mas também um dos mais frequentes no ruído.
- **Cenários:** Depois de uma alta, perto de resistência ou da máxima de 52 semanas.; Com volume acima da média na segunda vela.; Perde força em mercado lateral, onde engolfos se alternam sem consequência.
- **Combina com:** enforcado; estrela-cadente; estrela-noite; volume-anomalo
- **Neste painel:** Vela anterior de alta, atual de baixa, abertura ≥ fechamento anterior e fechamento ≤ abertura anterior. Aparece ~8,8 vezes por janela no ruído.

## Harami (vela dentro)

- **Fundamento:** O corpo de hoje cabe inteiro dentro do corpo de ontem. "Harami" é "grávida" em japonês: a vela grande "carrega" a pequena. Mostra que o movimento forte da véspera não teve continuidade.
- **Indica:** Perda de força e possível pausa. Não indica direção por si só: é a vela seguinte que diz se o movimento anterior retoma ou se reverte.
- **Cenários:** Depois de uma vela longa no fim de uma tendência.; Quando a vela de dentro é um doji (harami cross), a leitura de indecisão é mais forte.; Em janela curta é quase inútil: é o padrão mais comum no ruído deste painel.
- **Combina com:** doji; engolfo-alta; engolfo-baixa; estrela-manha; estrela-noite
- **Neste painel:** Corpo atual contido no corpo anterior. Aparece ~16 vezes por janela de 63 velas aleatórias — uma a cada quatro. Encontrá-lo não é informação.

## Estrela da manhã

- **Fundamento:** Três velas: uma baixa forte, uma vela de corpo pequeno (indecisão) e uma alta que recupera mais da metade da primeira. Conta a história completa de uma reversão — venda, empate e retomada compradora.
- **Indica:** Possível fundo. É considerado mais confiável que padrões de uma vela porque já traz a própria confirmação na terceira vela.
- **Cenários:** Depois de uma queda clara, perto de suporte ou da mínima de 52 semanas.; Mais forte quando a vela do meio é um doji e a terceira vem com volume alto.; A calibragem deste painel mostrou vantagem aparente mesmo no ruído: confira a taxa-base e o tamanho da amostra antes de confiar.
- **Combina com:** doji; martelo; engolfo-alta; marubozu-alta; volume-anomalo
- **Neste painel:** 1ª vela de baixa com corpo grande, 2ª de corpo pequeno, 3ª de alta fechando acima do meio da 1ª.

## Estrela da noite

- **Fundamento:** Espelho da estrela da manhã: uma alta forte, uma vela de indecisão e uma baixa que devolve mais da metade da primeira. Compradores dominaram, empataram e depois perderam o controle.
- **Indica:** Possível topo. Como a estrela da manhã, já contém a própria confirmação na terceira vela.
- **Cenários:** Depois de uma alta clara, perto de resistência ou da máxima de 52 semanas.; Mais forte quando a vela do meio é um doji ou uma estrela cadente.; Em preço bruto, confira se a terceira vela não é dia ex-dividendos.
- **Combina com:** doji; estrela-cadente; enforcado; engolfo-baixa; marubozu-baixa
- **Neste painel:** 1ª vela de alta com corpo grande, 2ª de corpo pequeno, 3ª de baixa fechando abaixo do meio da 1ª.

## Gap de abertura (alerta)

- **Fundamento:** O pregão abriu longe do fechamento anterior, sem negócios no meio. Acontece quando surge informação fora do horário de negociação — resultado, fato relevante, cenário externo — ou quando um provento sai do preço.
- **Indica:** Que algo mudou entre um pregão e outro. Em preço bruto, um gap de baixa na data ex pode ser só o dividendo ou o desdobramento, e não venda de verdade.
- **Cenários:** Gap com volume alto depois de notícia costuma marcar o início de um movimento.; Gap em direção contrária à tendência, sem volume, costuma ser "fechado" nos dias seguintes.; Sempre compare com o preço ajustado antes de tirar conclusão.
- **Combina com:** volume-anomalo; marubozu-alta; marubozu-baixa
- **Neste painel:** Abertura diferente do fechamento anterior em mais de 2%.

## Volume anômalo (alerta)

- **Fundamento:** Volume é quantas ações trocaram de mão. Muito acima da média significa que muita gente concordou em negociar naqueles preços — o movimento teve participação.
- **Indica:** Que o movimento daquele dia foi validado por muitos participantes. Mas volume alto também aparece por motivos mecânicos: vencimento de opções, rebalanceamento de índice, leilão de fechamento.
- **Cenários:** Como confirmação de padrões de reversão (martelo, engolfo, estrelas) e de rompimentos.; Confira o calendário: vencimento de opções e rebalanceamento de índices geram volume sem opinião sobre o preço.
- **Combina com:** engolfo-alta; engolfo-baixa; martelo; estrela-manha; estrela-noite; gap
- **Neste painel:** Volume maior que 2x a média dos 20 pregões anteriores.

## Liquidez baixa (alerta)

- **Fundamento:** Poucos negócios no dia. Com pouca gente negociando, um único comprador ou vendedor consegue mover o preço, e o desenho da vela pode refletir uma ordem isolada.
- **Indica:** Que a vela daquele dia é pouco confiável e que o preço mostrado pode não ser executável na prática — o spread consome o movimento.
- **Cenários:** Desconsidere padrões que se formam em dia de liquidez baixa.; Comum em feriados de outros mercados, véspera de feriado e ativos pouco negociados.
- **Combina com:** doji; gap
- **Neste painel:** Volume menor que 30% da média dos 20 pregões anteriores.
