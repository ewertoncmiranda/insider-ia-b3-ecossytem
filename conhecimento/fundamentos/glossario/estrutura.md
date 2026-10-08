---
tipo: fundamentos
colecao: glossario
titulo: "Tendência, suporte e resistência"
origem: painel-ativos-frontend/public/js/pages/GlossarioPage.js
disponivel_ate: 2000-01-01
gerado_em: 2026-10-08
hash: 7f00b7cf846641d6efbd7ed160550fc5a93c73286088edf36e96c808bff6116e
---

## Resumo

A leitura da estrutura do preço, que vem antes de qualquer indicador ou padrão de vela. Os padrões do grupo seguinte dependem destes termos.

## Tendência de alta e de baixa

Alta é uma sequência de topos e fundos cada vez mais altos; baixa, de topos e fundos cada vez mais baixos. Um candle sozinho não faz tendência: o que conta é o encadeamento dos extremos.

- **Exemplo:** Fundos em 30, 32 e 34 com topos em 33, 36 e 38 descrevem alta. Perder o último fundo (34) é o primeiro sinal de enfraquecimento.
- **Cuidado:** Marque os pivôs com uma regra fixa (ex.: maior máxima entre 5 pregões de cada lado); escolher os pontos no olho depois do fato cria a tendência que você queria ver.
- **Onde aparece no painel:** A posição no range de 52 semanas e o z-score da ficha dizem onde o preço está, não a direção da tendência - o sistema ainda não marca pivôs.

## Lateralização

Preço oscilando dentro de uma faixa, sem topos nem fundos progressivos. É o regime em que rompimentos falham com mais frequência e médias móveis dão mais sinais falsos.

- **Cuidado:** Muitos sinais em mercado lateral multiplicam custos de corretagem e spread sem ganho correspondente.

## Teoria de Dow

Leitura clássica que separa movimentos primários (meses a anos), secundários (semanas a meses, correções) e menores (dias). Deu origem à definição de tendência por topos e fundos.

- **Cuidado:** É uma forma de descrever o preço, não uma promessa de que o padrão se repete.

## Suporte e resistência

Suporte é uma região de preço onde as quedas vinham parando (compradores apareciam); resistência, onde as altas vinham parando (vendedores apareciam). São faixas aproximadas, não um preço exato.

- **Exemplo:** Uma ação que recuou três vezes perto de R$ 32 tem resistência na região de R$ 31,50 a R$ 32,50. Superada, essa região pode virar suporte - mas não necessariamente.
- **Cuidado:** Quanto mais óbvia a região, mais gente olha para ela e mais comuns são os falsos rompimentos.
- **Onde aparece no painel:** A máxima e a mínima de 52 semanas funcionam como resistência e suporte de referência na ficha e nos cartões de padrão da aba Velas.

## Linha de tendência e canal

Linha de tendência liga fundos ascendentes (alta) ou topos descendentes (baixa) e mostra inclinação e aceleração. Canal é o par de linhas paralelas que contém as oscilações.

- **Cuidado:** Não force a linha para o gráfico caber nela. Romper uma linha sozinha informa menos que uma mudança na sequência de topos e fundos.

## Falso rompimento

O preço atravessa um suporte ou resistência e volta logo para dentro da faixa anterior. Também chamado de armadilha: pega quem entrou no rompimento.

- **Exemplo:** Fecha a R$ 32,40 acima da resistência de R$ 32 e, dois pregões depois, está de volta a R$ 31,20.
- **Cuidado:** Defina antes o que é rompimento válido (fechamento acima da faixa, não só sombra) e registre as falhas, não apenas os casos que deram certo.
- **Onde aparece no painel:** O cartão de rompimento da aba Velas avisa quando o volume foi fraco - o caso mais comum de falso rompimento.

## Reteste

Depois de romper uma região, o preço volta até ela e a usa como apoio antes de seguir. Resistência rompida sendo testada como suporte é o caso clássico.

- **Cuidado:** Não presuma que o reteste vai acontecer: muitos rompimentos verdadeiros seguem sem voltar.

## Prazos operacionais (intradiário, swing, posição)

Intradiário: abre e fecha no mesmo dia, gráficos de minutos. Swing trade: dias a semanas, gráfico diário. Posição: meses, gráfico semanal. O mesmo padrão tem peso diferente em cada prazo.

- **Cuidado:** Leia do maior para o menor: uma alta no diário pode ser só um repique dentro de uma baixa no semanal. Trocar de prazo até concordar com a sua tese é timeframe shopping.
- **Onde aparece no painel:** O sistema trabalha com pregões diários (COTAHIST) e agrupa em semana e mês na aba Velas; não há dado intradiário.
