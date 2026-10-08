---
tipo: fundamentos
colecao: academico
titulo: "Gráficos, indicadores e execução"
origem: painel-ativos-frontend/public/js/estudos/glossarioAcademico.js
disponivel_ate: 2000-01-01
gerado_em: 2026-10-08
hash: f3aee61f5fb717544053baf99db6770eb6123d820d769985d92ee94053e6ffc8
---

## Resumo

Ferramentas para formular hipóteses sobre preços e negociação.

## Escala logarítmica

Escala em que distâncias iguais representam variações proporcionais iguais.

- **Exemplo:** Subir de 10 para 20 ocupa a mesma distância que subir de 20 para 40.
- **Cuidado:** A geometria de linhas pode mudar quando se troca a escala.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## LTA e LTB

Linhas de tendência de alta e de baixa usadas para representar a direção de fundos ou topos.

- **Exemplo:** Uma LTA pode ligar fundos ascendentes segundo uma regra definida.
- **Cuidado:** A escolha dos pontos pode ser subjetiva.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Pivô

Estrutura de movimentos e correções que pode sinalizar mudança ou continuidade da tendência, conforme a definição adotada.

- **Exemplo:** Uma regra pode exigir topo e fundo ascendentes antes da confirmação.
- **Cuidado:** Defina os critérios antes de avaliar o resultado.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## OCO — ombro-cabeça-ombro

Figura gráfica com três regiões de topo, sendo a central mais alta, interpretada em conjunto com a linha de pescoço.

- **Exemplo:** O estudo pode testar o rompimento da linha de pescoço após a formação.
- **Cuidado:** O reconhecimento visual é subjetivo e não garante reversão.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Ondas de Elliott

Abordagem que interpreta movimentos de mercado por estruturas de impulsos e correções.

- **Exemplo:** Duas contagens podem descrever de modos diferentes o mesmo gráfico.
- **Cuidado:** Registre regras e contagens alternativas para reduzir interpretação retrospectiva.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## IFR — Índice de Força Relativa (RSI)

Oscilador que compara a intensidade de ganhos e perdas em uma janela.

- **Exemplo:** Uma leitura elevada indica predominância recente de ganhos na fórmula adotada.
- **Cuidado:** Sobrecompra não obriga queda; tendências podem manter leituras extremas.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Estocástico

Oscilador que relaciona o fechamento à faixa entre máxima e mínima de uma janela.

- **Exemplo:** Fechamento próximo à máxima da janela tende a elevar o indicador.
- **Cuidado:** Parâmetros e suavizações mudam o resultado; extremos não são ordens.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## MACD

Indicador baseado na diferença entre médias móveis exponenciais, acompanhado por uma linha de sinal.

- **Exemplo:** A diferença entre MACD e sinal costuma ser exibida como histograma.
- **Cuidado:** Usa preços passados e pode produzir sinais alternados em lateralizações.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Bandas de Bollinger

Bandas em torno de uma média, com distância ligada ao desvio-padrão dos preços na janela.

- **Exemplo:** Bandas mais largas indicam maior dispersão nessa medida.
- **Cuidado:** Tocar uma banda não determina retorno à média.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Volume relativo

Volume observado dividido por uma referência de volume médio, conforme janela definida.

- **Exemplo:** Volume de 150 com média de 100 resulta em 1,5 vez.
- **Cuidado:** Compare períodos compatíveis; volume parcial do dia não equivale ao volume diário completo.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Microestrutura de mercado

Estudo dos mecanismos de negociação, formação de preços, liquidez e execução.

- **Exemplo:** Leilões e prioridade das ordens influenciam a execução.
- **Cuidado:** Velas diárias não mostram toda a dinâmica das ordens.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Tape reading

Leitura de registros de negócios e informações de ofertas para estudar a negociação em curto prazo.

- **Exemplo:** Comparar negócios executados com mudanças no book.
- **Cuidado:** Exige dados específicos; não pode ser reconstruído de modo completo a partir de OHLC diário.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Book de ofertas

Registro de ofertas de compra e venda disponíveis nos níveis de preço exibidos.

- **Exemplo:** Uma oferta limitada pode permanecer na fila até ser executada ou cancelada.
- **Cuidado:** Ofertas exibidas não equivalem a negócios efetivamente realizados.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Times & trades

Sequência de negócios executados com informações como horário, preço e quantidade.

- **Exemplo:** Uma lista de execuções permite observar a atividade ao longo do pregão.
- **Cuidado:** O registro não revela necessariamente a intenção dos participantes.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Volume at price — volume por preço

Distribuição do volume negociado por níveis de preço.

- **Exemplo:** Uma faixa pode concentrar mais negócios do que outras.
- **Cuidado:** Volume por vela diária não contém sozinho essa distribuição.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## HFT — negociação de alta frequência

Conjunto de práticas automatizadas com baixa latência e grande velocidade de envio e gestão de ordens.

- **Exemplo:** Estratégias podem atuar na provisão de liquidez.
- **Cuidado:** Nem todo robô é HFT; velocidade não garante rentabilidade.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Spread

Diferença entre a melhor oferta de venda e a melhor oferta de compra em um momento.

- **Exemplo:** Compra a 10,00 e venda a 10,02: spread de 0,02.
- **Cuidado:** Spreads podem aumentar quando a liquidez diminui.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Slippage — deslizamento de preço

Diferença entre o preço de execução esperado e o efetivamente obtido.

- **Exemplo:** Um stop acionado a 20 pode executar a 19,80.
- **Cuidado:** Simulações sem deslizamento podem superestimar resultados.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.
