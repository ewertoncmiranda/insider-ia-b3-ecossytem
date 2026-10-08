---
tipo: fundamentos
colecao: glossario
titulo: Os documentos que a empresa e obrigada a publicar
origem: painel-ativos-frontend/public/js/pages/GlossarioPage.js
disponivel_ate: 2000-01-01
gerado_em: 2026-10-08
hash: 27fcd2894fbb73f80011df02479836f6587660fa3b439e182cd473a917874c8c
---

## Resumo

As siglas dos arquivos da CVM que alimentam este sistema.

## DFP

O "boletim anual" da empresa. Sai uma vez por ano, com os numeros auditados do exercicio fechado.

- **Sigla:** Demonstracoes Financeiras Padronizadas
- **Onde aparece no painel:** Origem de praticamente todo indicador contabil exibido.

## ITR

A mesma coisa, mas a cada 3 meses: mais rapida e menos auditada que a DFP.

- **Sigla:** Informacoes Trimestrais
- **Onde aparece no painel:** Ainda nao usada - e o que falta para calcular TTM.

## FCA

Quem e a empresa: CNPJ, endereco e quais tickers ela tem na B3.

- **Sigla:** Formulario Cadastral
- **Onde aparece no painel:** E o que permite ligar o ticker WEGE3 ao CNPJ da WEG.

## FRE

O dossie completo da companhia. Aqui e usado por um motivo especifico: e a fonte confiavel da quantidade de acoes.

- **Sigla:** Formulario de Referencia
- **Onde aparece no painel:** Denominador de LPA e VPA.

## Exercicio social

O "ano" contabil da empresa. Quase sempre de janeiro a dezembro.

- **Onde aparece no painel:** O campo "periodo" nos fundamentos e a data de fechamento dele.

## Reapresentacao

Quando a empresa republica um balanco corrigido. Por isso todo arquivo tem um numero de versao, e so a maior vale.

## Consolidado x individual

O consolidado soma a empresa e todas as suas controladas; o individual e so a matriz. Comparacoes de mercado usam o consolidado.

- **Onde aparece no painel:** O campo "grupo" indica qual foi usado (con ou ind).

## IPE

A base da CVM que lista todo documento eventual entregue pelas companhias: fatos relevantes, comunicados, avisos, atas. Cada linha traz o link oficial do documento.

- **Sigla:** Informações Periódicas e Eventuais
- **Onde aparece no painel:** Fonte da aba Comunicados. A CVM a republica cerca de uma vez por semana, por isso a aba informa até que data há dados.

## Fato relevante

Comunicado obrigatório sobre qualquer decisão ou acontecimento capaz de influenciar o preço da ação ou a decisão de investir: aquisição, mudança de controle, resultado fora do esperado, renegociação de dívida. Deve ser divulgado a todos ao mesmo tempo.

- **Cuidado:** Nem todo fato relevante é notícia boa ou ruim; é o fato que a companhia considera capaz de mover o preço. Leia o documento antes de tirar conclusão.
- **Onde aparece no painel:** Aparece primeiro na edição semanal da aba Comunicados, em vermelho.

## Comunicado ao mercado

Informação que a companhia decide divulgar sem que seja fato relevante: esclarecimentos sobre notícias, contratos, eventos operacionais.

## Aviso aos acionistas

Informação dirigida a quem tem a ação: datas de pagamento de proventos, direito de subscrição, prazos de assembleia.

## RAD

O sistema da CVM onde os documentos das companhias ficam disponíveis. O link "Abrir documento na CVM" leva direto a ele.

- **Sigla:** Rede de Atendimento Digital (ENET)
