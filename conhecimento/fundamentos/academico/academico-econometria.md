---
tipo: fundamentos
colecao: academico
titulo: Econometria e modelos quantitativos
origem: painel-ativos-frontend/public/js/estudos/glossarioAcademico.js
disponivel_ate: 2000-01-01
gerado_em: 2026-10-08
hash: 3dd3e8ef3d76c5e8d476068060a23b254c812e70e69fae1a1952bf0e9216bd81
---

## Resumo

Premissas e diagnósticos para interpretar estudos empíricos.

## MQO — Mínimos Quadrados Ordinários

Método que estima coeficientes minimizando a soma dos quadrados dos resíduos.

- **Exemplo:** Estimar associação entre retorno e fatores explicativos.
- **Cuidado:** Inferência válida depende de premissas e de erros-padrão adequados.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Resíduo da regressão

Diferença entre o valor observado e o previsto pelo modelo.

- **Exemplo:** Retorno real de 2% e previsto de 1,5% produzem resíduo de 0,5 ponto.
- **Cuidado:** Padrões nos resíduos indicam possível inadequação do modelo.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Heterocedasticidade

Variação não constante da dispersão dos erros entre observações.

- **Exemplo:** Erros podem aumentar em períodos de alta volatilidade.
- **Cuidado:** Pode invalidar erros-padrão usuais; não é corrigida apenas adicionando variáveis.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Autocorrelação

Dependência entre erros ou valores da série em momentos diferentes.

- **Exemplo:** Resíduo positivo tende a ser seguido por outro positivo.
- **Cuidado:** Ignorá-la pode distorcer inferência e avaliação preditiva.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Multicolinearidade

Forte relação entre variáveis explicativas que dificulta separar seus efeitos.

- **Exemplo:** Duas taxas de juros muito semelhantes entram juntas no modelo.
- **Cuidado:** Não implica previsão ruim, mas pode tornar coeficientes instáveis.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## R² — coeficiente de determinação

Proporção da variação observada explicada pelo modelo na amostra, sob sua definição.

- **Exemplo:** R² de 0,40 indica ajuste de 40% da variação na amostra.
- **Cuidado:** R² alto não comprova causalidade, validade fora da amostra ou especificação correta.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Dados em painel

Dados que acompanham várias unidades ao longo do tempo.

- **Exemplo:** Observar empresas por diversos trimestres.
- **Cuidado:** É preciso tratar dependência temporal e entre unidades.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Efeitos fixos e aleatórios

Modelos de painel que tratam diferenças não observadas entre unidades de maneiras distintas.

- **Exemplo:** Efeito fixo controla características invariantes de cada empresa.
- **Cuidado:** A escolha depende das hipóteses e não apenas de qual modelo tem melhor ajuste.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Markov switching — mudança de regime

Modelo em que parâmetros dependem de um estado latente que muda segundo probabilidades de transição.

- **Exemplo:** Inflação pode alternar entre regimes de alta e baixa persistência.
- **Cuidado:** Regimes são inferidos pelo modelo e não fatos diretamente observados.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Componentes principais

Transformação que resume variáveis correlacionadas em combinações que capturam variação.

- **Exemplo:** Nível, inclinação e curvatura podem resumir movimentos da curva.
- **Cuidado:** Componentes maximizam variância, não necessariamente relevância econômica.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.
