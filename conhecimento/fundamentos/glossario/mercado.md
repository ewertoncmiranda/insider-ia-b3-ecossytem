---
tipo: fundamentos
colecao: glossario
titulo: Onde as acoes sao negociadas
origem: painel-ativos-frontend/public/js/pages/GlossarioPage.js
disponivel_ate: 2000-01-01
gerado_em: 2026-10-08
hash: 6abc8971cb4353f3a3acce3f9a9542088f22c7f0b5f76c81c4c7e29cf3e34d6f
---

## Resumo

O basico: o que voce compra, onde, e quem fiscaliza.

## Acao

Um pedaco da empresa. Quem tem 1 acao de 1.000 existentes e dono de 0,1% dela - dos lucros e tambem dos prejuizos.

- **Onde aparece no painel:** É o que você consulta na aba Gestão.

## B3

A bolsa de valores brasileira, onde as acoes sao compradas e vendidas. Nome antigo: Bovespa.

## Ticker (codigo de negociacao)

O apelido da acao no pregao, tipo PETR4 ou WEGE3. As letras identificam a empresa e o numero diz o tipo de acao.

- **Onde aparece no painel:** E o que voce digita no campo de busca.

## ON / PN / Unit

O numero final do ticker. 3 = ordinaria (da direito a voto nas assembleias). 4 = preferencial (normalmente sem voto, mas com preferencia no recebimento de dividendos). 11 = unit, um pacote que junta as duas.

## Pregao

O dia de negociacao. "Fechamento do pregao" e o preco do ultimo negocio daquele dia.

- **Onde aparece no painel:** Cada linha da tabela de historico e um pregao.

## COTAHIST

O arquivo oficial de series historicas de cotacoes publicado pela propria B3 - o registro definitivo do que foi negociado em cada pregao, para todos os instrumentos (acoes, opcoes, termo, fracionario), desde a decada de 1980 ate hoje. E a fonte "verdade absoluta" de preco no mercado brasileiro: quando BRAPI ou qualquer outra fonte secundaria diverge, o COTAHIST e quem desempata.

- **Sigla:** Cotacoes Historicas (arquivo da B3)
- **Exemplo:** Formato texto de largura fixa (posicional, nao CSV/JSON) - cada linha tem campos em posicoes de caractere fixas: codigo BDI (tipo de mercado), ticker, nome resumido da empresa, preco de abertura/maximo/minimo/medio/ultimo, melhor oferta de compra/venda, quantidade de negocios, quantidade de titulos negociados, volume financeiro, entre outros. Distribuido em arquivos anuais (COTAHIST_A{ano}.ZIP, ~80-90 MB cada), tambem existe versao mensal e diaria. Download direto, sem chave nem cadastro: bvmf.bmfbovespa.com.br/InstDados/SerHist/.
- **Cuidado:** O preco no COTAHIST e BRUTO (nao ajustado por proventos/desdobramentos) - um dividendo ou split aparece como salto no preco de um dia pro outro, sem ninguem ter vendido nada. Ajustar isso exige cruzar com a base de proventos/eventos corporativos separadamente (ver Preco ajustado e Provento neste glossario) - o arquivo em si nao devolve preco ja ajustado.
- **Onde aparece no painel:** Tabela cotacao_b3_diaria (mysql-migrations V6) - carregada a partir dos arquivos anuais desde 2016, usada pra checagem cruzada contra a BRAPI e como fonte de preco do backtest (o motor de avaliacao usa preco oficial, nao o da API de cotacao em tempo quase real).

## Companhia aberta

Empresa autorizada a vender acoes ao publico. Em troca, e obrigada por lei a publicar seus numeros - e essa obrigacao que torna este sistema possivel.

## CVM

Autarquia federal criada pela Lei 6.385/1976, vinculada ao Ministerio da Fazenda, responsavel por regular, fiscalizar e disciplinar o mercado de valores mobiliarios brasileiro (acoes, debentures, fundos, derivativos). Equivalente brasileiro da SEC americana. Missao legal: proteger o investidor, assegurar o funcionamento eficiente do mercado e garantir acesso a informacao adequada - e essa terceira obrigacao que torna este sistema possivel: toda companhia aberta e obrigada por lei a publicar seus numeros, e a CVM os disponibiliza de graca.

- **Sigla:** Comissao de Valores Mobiliarios
- **Exemplo:** Poderes praticos: registra companhias abertas e ofertas publicas (IPO), edita normas (as "Instrucoes"/"Resolucoes CVM" - ex.: Resolucao CVM 20/2021, que rege a certificacao de analistas), investiga e pune infracoes (processo administrativo sancionador, que pode culminar em multa, inabilitacao ou ate esfera penal em casos de fraude/insider trading).
- **Cuidado:** A CVM e o orgao regulador - nao o mesmo que a B3 (a bolsa, empresa privada que opera o ambiente de negociacao) nem que o Banco Central (que regula o sistema financeiro/bancario e a politica monetaria). Confundir os tres e erro comum entre iniciantes.
- **Onde aparece no painel:** Fonte de todos os fundamentos contabeis deste sistema (via etl-fundamentos-cvm) e dos comunicados oficiais (aba Comunicados). Dois canais: o Portal de Dados Abertos (dados.cvm.gov.br, machine-readable, gratis, sem cadastro - o que este sistema consome) e o RAD/ENET (Rede de Atendimento Digital, onde a propria empresa protocola os documentos e o publico le em PDF).

## Acoes em tesouraria

Acoes que a propria empresa recomprou e mantem guardadas. Nao valem dividendo nem voto, entao saem da conta na hora de dividir o lucro por acao.

- **Onde aparece no painel:** Descontadas do denominador de LPA e VPA.

## Acionista controlador e minoritario

O controlador manda na empresa; o minoritario so acompanha. Importa aqui porque parte do lucro de um grupo pertence a socios de outras empresas dele - e o mercado calcula os indicadores so sobre a parte do controlador.

- **Onde aparece no painel:** Por isso o ROE que mostramos usa o lucro do controlador.
