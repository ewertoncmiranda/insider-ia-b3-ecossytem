---
tipo: fundamentos
colecao: academico
titulo: Curvas de juros e macrofinanças
origem: painel-ativos-frontend/public/js/estudos/glossarioAcademico.js
disponivel_ate: 2000-01-01
gerado_em: 2026-10-08
hash: a55e0292464f5effd2411a73c7fbf7d464862ea8c0f08cbbfb4f8d1f66611e79
---

## Resumo

Vocabulário para ler estruturas a termo, expectativas e dívida pública.

## ETTJ — Estrutura a Termo da Taxa de Juros

Relação entre taxas de juros e prazos para instrumentos comparáveis em uma data.

- **Exemplo:** Uma curva pode mostrar taxas para 1, 2 e 5 anos.
- **Cuidado:** A curva incorpora expectativas, prêmios de risco, liquidez e convenções; não é previsão pura.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Taxa spot — taxa à vista

Taxa associada a um fluxo entre a data atual e um vencimento específico.

- **Exemplo:** A taxa zero de dois anos desconta um pagamento único nesse prazo.
- **Cuidado:** Compare taxas com a mesma base de dias, capitalização, moeda e risco.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Taxa forward — taxa a termo

Taxa implícita entre duas datas futuras, derivada de taxas para prazos diferentes.

- **Exemplo:** Taxas de um e dois anos permitem obter a taxa implícita do segundo ano.
- **Cuidado:** Não equivale necessariamente à taxa que será observada no futuro.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Vértice da curva

Prazo ou data de referência em que a curva possui um valor observado ou calculado.

- **Exemplo:** Um vencimento de 252 dias úteis pode ser um vértice.
- **Cuidado:** Vértices de fontes diferentes podem usar calendários e convenções incompatíveis.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Fator de desconto

Valor presente de uma unidade monetária a receber no futuro.

- **Exemplo:** Fator 0,90 significa que uma unidade futura vale 0,90 hoje sob aquela curva.
- **Cuidado:** Depende da taxa, prazo e convenção de capitalização.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Interpolação

Procedimento para estimar valores entre vértices conhecidos.

- **Exemplo:** Estimar a taxa de 18 meses usando vértices de 1 e 2 anos.
- **Cuidado:** Métodos diferentes podem produzir preços e sensibilidades diferentes.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Nelson-Siegel-Svensson

Família paramétrica usada para representar nível, inclinação e curvatura da estrutura a termo.

- **Exemplo:** Fatores estimados ajustam uma curva suave aos dados observados.
- **Cuidado:** Bom ajuste histórico não garante previsão nem elimina erro de especificação.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Inflação implícita

Diferença aproximada entre taxas nominais e reais comparáveis, acrescida de efeitos de prêmio e liquidez.

- **Exemplo:** Comparar curva prefixada e curva indexada ao IPCA.
- **Cuidado:** Não deve ser chamada diretamente de expectativa de inflação.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Juro real neutro

Taxa real compatível, em um modelo, com economia no potencial e inflação estável.

- **Exemplo:** Analistas estimam a taxa neutra para avaliar a orientação monetária.
- **Cuidado:** É variável não observável e depende do método.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Prêmio de risco

Remuneração adicional exigida por incerteza, liquidez, crédito ou outros riscos.

- **Exemplo:** Um título menos líquido pode pagar taxa maior.
- **Cuidado:** Não é diretamente observável sem modelo ou referência comparável.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Resultado primário

Receitas menos despesas do governo antes dos juros da dívida.

- **Exemplo:** Superávit primário contribui para reduzir a necessidade de financiamento.
- **Cuidado:** Não representa sozinho o resultado nominal nem garante queda da dívida/PIB.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Condição de transversalidade

Condição teórica que impede financiar indefinidamente a dívida apenas com nova dívida sem respaldo fiscal.

- **Exemplo:** A dívida descontada não pode crescer sem limite no horizonte do modelo.
- **Cuidado:** Sua verificação empírica depende de hipóteses sobre juros, crescimento e política futura.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Regra fiscal

Restrição permanente sobre gastos, resultados, receitas ou dívida usada para orientar a política fiscal.

- **Exemplo:** Um teto de despesa limita o crescimento de determinada base de gastos.
- **Cuidado:** Regras precisam combinar credibilidade, transparência e resposta a choques.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.

## Dominância fiscal

Situação em que restrições fiscais condicionam a política monetária e podem prejudicar o controle da inflação.

- **Exemplo:** Juros maiores podem piorar a dívida e alterar expectativas em um quadro fiscal frágil.
- **Cuidado:** O diagnóstico exige evidência; dívida elevada isoladamente não o comprova.
- **Onde aparece no painel:** Trilha de Estudos e exercícios de pesquisa. Nem todos os cálculos estão disponíveis no painel.
