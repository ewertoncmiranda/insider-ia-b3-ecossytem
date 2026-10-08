---
tipo: fundamentos
colecao: glossario
titulo: Padroes de grafico
origem: painel-ativos-frontend/public/js/pages/GlossarioPage.js
disponivel_ate: 2000-01-01
gerado_em: 2026-10-08
hash: 709845f0181e9d6c793dc054d1f85a24b4291279dafd15f483936d0255814eae
---

## Resumo

Os desenhos que traders procuram no grafico. O raciocinio por tras de cada um, e quando confiar, esta na aba Padroes e armadilhas.

## Corpo e sombra

O corpo da vela vai da abertura ao fechamento e mede conviccao; a sombra e o que passou disso e mede rejeicao. Sombra longa significa que o preco chegou la e nao ficou.

- **Onde aparece no painel:** Cada barra do grafico da aba Candles.

## Martelo

Vela de corpo pequeno com sombra inferior de pelo menos o dobro do corpo: derrubaram o preco e os compradores absorveram.

- **Onde aparece no painel:** So sugere reversao se aparecer depois de uma queda.

## Enforcado

O mesmo desenho do martelo, mas aparecendo depois de uma alta. A forma nao muda; o que muda e o contexto.

## Engolfo

O corpo de uma vela engole inteiro o da anterior, indicando que o lado oposto tomou conta da sessao.

- **Onde aparece no painel:** Vale mais quando vem com volume acima da media.

## Doji

Abertura praticamente igual ao fechamento: a sessao terminou empatada. Sinal de indecisao.

- **Onde aparece no painel:** So informa alguma coisa quando interrompe uma tendencia definida.

## Estrela da manha / da noite

Sequencia de tres velas — tendencia, indecisao, reversao. A terceira e a que confirma.

## Topo duplo e fundo duplo

Dois testes do mesmo nivel de preco sem conseguir rompe-lo. O gatilho nao e o segundo topo, e o rompimento da linha tracada no fundo entre os dois.

## Ombro-Cabeca-Ombro

Tres picos, com o do meio mais alto, sugerindo reversao de tendencia.

- **Sigla:** OCO
- **Onde aparece no painel:** Leva de 3 a 6 meses para se formar: use os períodos de 1 ano ou 5 anos da aba Velas (pregões do banco desde 2016). O sistema não detecta OCO automaticamente.

## Triangulo

Ascendente: topos no mesmo nivel e fundos subindo. Descendente: o inverso. Simetrico: os dois convergem, e rompe para qualquer lado.

## Retângulo

Faixa lateral com topos e fundos em níveis parecidos: uma pausa em que compradores e vendedores se equilibram. O significado vem do lado por onde o preço sai da faixa.

- **Cuidado:** Não presuma continuação só pela aparência: o retângulo rompe para qualquer lado.

## Cunha

Duas linhas convergentes inclinadas para o mesmo lado. Cunha ascendente (topos e fundos subindo cada vez mais devagar) costuma ser lida como perda de força da alta; descendente, o inverso.

- **Cuidado:** Definições vagas de onde começa e termina a cunha criam viés de seleção: qualquer oscilação vira cunha depois do fato.

## Bandeira e flamula

Pausa curta logo depois de um movimento forte. Padrao de continuacao, nao de reversao — confundir os dois e erro comum.

## Linha de pescoco

A linha que liga os fundos de uma formacao (topo duplo, OCO). O rompimento dela e o que confirma a figura.

## Golden cross e death cross

Cruzamento da media de 50 periodos com a de 200. Golden cross e a de 50 subindo acima da de 200; death cross o contrario.

- **Onde aparece no painel:** Precisa de 200 pregões: dá para observar nos períodos longos da aba Velas (banco desde 2016), mas o sistema não calcula nem desenha as médias de 50 e 200.

## Gap

Salto entre o fechamento de um dia e a abertura do seguinte, sem negocio no meio. Atencao: dividendo e desdobramento produzem gap falso no preco nao ajustado.

## Rompimento

Quando o preco atravessa um nivel que vinha segurando. Rompimento com volume fraco e suspeito: poucos participantes validaram o preco novo.
