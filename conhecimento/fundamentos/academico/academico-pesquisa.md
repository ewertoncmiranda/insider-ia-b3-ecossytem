---
tipo: fundamentos
colecao: academico
titulo: Estatística e pesquisa reproduzível
origem: painel-ativos-frontend/public/js/estudos/glossarioAcademico.js
disponivel_ate: 2000-01-01
gerado_em: 2026-10-08
hash: 93f2d9942824672221b25ddea37abe2207e30583839101db50c1531a44b57432
---

## Resumo

Termos para comparar padrões sem confundir coincidência com evidência.

## Hipótese testável

Afirmação traduzida em condições e medidas que permitem confrontá-la com dados.

- **Exemplo:** Engolfos após quedas apresentam retorno de cinco dias diferente de situações comparáveis?
- **Cuidado:** Especifique universo, regra, horizonte e referência antes do teste.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Taxa-base

Frequência de um resultado no grupo de referência usado na comparação.

- **Exemplo:** Se a referência sobe 65% das vezes, acerto de 60% do padrão não é superior nessa métrica.
- **Cuidado:** A referência deve ter condições comparáveis.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Probabilidade condicional

Probabilidade de um evento considerando que outra condição ocorreu.

- **Exemplo:** Probabilidade de alta dado que houve engolfo após queda.
- **Cuidado:** Associação não demonstra causa nem garante o próximo resultado.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Dispersão e desvio-padrão

Medidas de variabilidade dos valores em torno de uma referência; o desvio-padrão usa desvios em relação à média.

- **Exemplo:** Retornos com mesma média podem ter dispersões muito diferentes.
- **Cuidado:** Uma única medida não descreve toda a distribuição nem suas caudas.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Intervalo de confiança

Faixa produzida por um procedimento estatístico para expressar a incerteza da estimativa sob suas premissas.

- **Exemplo:** Um procedimento de 95% cobre o parâmetro em 95% de repetições sob as condições do modelo.
- **Cuidado:** Não é garantia de retorno nem probabilidade direta atribuída ao parâmetro fixo.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Reamostragem — bootstrap

Construção de novas amostras a partir dos dados observados para estudar a variabilidade de estimativas.

- **Exemplo:** Recalcular uma média em muitas amostras reconstituídas.
- **Cuidado:** Séries temporais dependentes podem exigir blocos; reamostrar não corrige dados enviesados.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Backtest

Simulação histórica de regras de decisão e execução.

- **Exemplo:** Aplicar regras congeladas a preços passados com custos.
- **Cuidado:** Não garante resultado futuro e pode conter informação que não estava disponível na época.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Fora da amostra

Avaliação em dados que não participaram da criação ou ajuste do modelo.

- **Exemplo:** Desenvolver em um período e testar em outro posterior.
- **Cuidado:** Reutilizar repetidamente o teste para ajustar a estratégia contamina a avaliação.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Walk-forward

Validação em janelas temporais sucessivas, usando o passado para desenvolver e o período seguinte para avaliar.

- **Exemplo:** Ajustar em uma janela e avaliar no trimestre posterior, repetindo o processo.
- **Cuidado:** Todos os parâmetros e custos devem seguir uma regra previamente definida.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Sobreajuste — overfitting

Adaptação excessiva às particularidades dos dados de desenvolvimento, incluindo ruído.

- **Exemplo:** Escolher entre centenas de calibragens apenas a que teve o melhor passado.
- **Cuidado:** Excelente resultado histórico pode não se repetir fora da amostra.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Viés de sobrevivência

Distorção por analisar apenas os participantes que permaneceram disponíveis.

- **Exemplo:** Testar apenas empresas atualmente listadas e ignorar as que saíram.
- **Cuidado:** O universo histórico deve refletir o que existia em cada data.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Informação futura — look-ahead bias

Uso, em uma decisão simulada, de informação ainda desconhecida naquele momento.

- **Exemplo:** Negociar em janeiro usando balanço publicado em março.
- **Cuidado:** Use a data de disponibilidade, não só o período de referência.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Múltiplos testes

Realização de muitas comparações, aumentando a chance de encontrar resultados extremos por acaso.

- **Exemplo:** Testar cem padrões e divulgar apenas o vencedor.
- **Cuidado:** Registre todas as tentativas e valide em dados separados.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Dependência entre observações

Situação em que resultados compartilham influências ou informação e não podem ser tratados como independentes.

- **Exemplo:** Cem sinais no mesmo dia podem refletir um único choque de mercado.
- **Cuidado:** Amostra numerosa não significa igual número de experimentos independentes.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Benchmark — referência de comparação

Medida, grupo ou estratégia escolhida para avaliar um resultado.

- **Exemplo:** Comparar uma estratégia com exposição semelhante ao mercado.
- **Cuidado:** A referência precisa ser adequada ao risco, horizonte e exposição.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Pesquisa reproduzível

Estudo cujos dados, regras e passos permitem refazer os resultados.

- **Exemplo:** Guardar fontes, versões, parâmetros, períodos e critérios de exclusão.
- **Cuidado:** Reprodução não prova que as premissas são corretas; permite examiná-las.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.
