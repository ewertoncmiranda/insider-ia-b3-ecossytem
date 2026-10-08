# SPEC — insider-ia-b3-ecossytem

**Versão:** 0.1.0 · **Status:** PLANEJADO · **Criada em:** 2026-10-07
**Público:** desenvolvedores humanos e agentes de IA (Claude, Codex, outros).

Serviço de IA local do ecossistema B3: produz a **opinião por horizonte** de cada ativo a partir de evidências determinísticas, **skills** versionadas e **RAG** com fontes. O modelo de linguagem é trocável e só redige; o conhecimento mora nas skills, nas fichas `.md` e no índice do RAG, nunca nos pesos do modelo.

---

## Estados comuns

`PLANEJADO` · `EM ANDAMENTO (agente/branch, data)` · `IMPLEMENTADO` · `VERIFICADO` · `BLOQUEADO (motivo)`. IDs são estáveis: nunca renumerar nem apagar.

## 1. Como usar este arquivo (protocolo para agentes)

Mesmo protocolo dos repositórios irmãos (`gerar-insights`, `gestor-ativos-brutos`, `etl-fundamentos-cvm`, `painel-ativos-frontend`, `infra-b3-ecossytem`).

1. Leia as seções 2 a 8 antes de codar. Toda mudança cita um `REQ-`, `NFR-`, `TASK-` ou `DEC-`.
2. Coordenação: **hub** em `infra-b3-ecossytem/SPEC.md` seção 1A. Ao pegar tarefa, marque `EM ANDAMENTO` lá e aqui.
3. Commit só em `feature-*`, arquivo por arquivo (nunca `git add -A`); PRs abrem automaticamente.
4. Este serviço **não cria tabelas**: o schema é do Flyway da infra (`opiniao_ia` = V22).
5. Nenhum rótulo de recomendação sem aviso de regra experimental (Res. CVM 20/2021).

Fluxo: `Spec → Plano → Tarefas → Implementação → Verificação → Atualizar Spec`.

---

## 2. Contexto e motivação

- Hoje a opinião por horizonte vive em `gerar-insights/app/opiniao` (Sessão 02): o prompt, a validação e a chamada ao Ollama estão acoplados ao worker.
- O modelo em uso (`qwen2.5:1.5b-instruct`) é pequeno: mistura campos, repete evidências e às vezes contradiz o próprio dado (observado em PETR4, 2026-10-06).
- Evidência empírica (COTAHIST 2016–2026, ~81 mil observações semanais): o quintil de maior momentum em 20 pregões bateu o mercado nos 5 pregões seguintes em **49,1%** das semanas; o de menor, em **47,2%**. Nenhuma regra atual tem vantagem distinguível no backtest. Logo, o sistema **descreve e contextualiza**; não promete previsão.
- Consultas históricas longas no MySQL custam 37–73 s. Conhecimento de anos fechados deve ser **pré-calculado uma vez** e consultado como arquivo.

## 3. Princípios

| ID | Princípio |
|---|---|
| P-1 | O modelo não sabe nada de bolsa; tudo que afirma vem de **evidências** (números do dia), **skills** (como interpretar) ou **RAG** (trechos com fonte). |
| P-2 | Toda afirmação cita `evidencia_id` ou `trecho_id`; número citado tem de existir nas entradas. Saída inválida ⇒ resposta por regra (`origem = REGRA`). |
| P-3 | Desacoplado: só HTTP dentro da rede Docker; nenhum outro serviço conhece prompt ou modelo. |
| P-4 | Ponto no tempo: nada com data de disponibilidade posterior ao pregão analisado entra no contexto. |
| P-5 | Sem internet: modelos, índices e fichas em volumes/Git locais. |
| P-6 | Trocar o modelo é trocar uma variável de ambiente; conhecimento não se perde. |

---

## 4. Arquitetura

### 4.1 Componentes

| Serviço | Papel | Tecnologia |
|---|---|---|
| `ia-opiniao` (este repo) | Orquestrador: seleciona skills, busca no RAG, chama o modelo, valida, devolve | Python 3.11+, FastAPI |
| `ollama` | Inferência (chat e embeddings) | `ollama/ollama` (hoje 0.40.0, em `infra/compose.ia.yml`) |
| `vetores` | Índice do RAG | Qdrant em container; alternativa inicial: SQLite + `sqlite-vec` embutido (DEC-IA-02) |
| `gerar-insights` | Dono dos números: monta evidências e grava `opiniao_ia` | existente |
| MySQL | Fonte de verdade; leitura para gerar fichas | existente |

### 4.2 Fluxo

```
gerar-insights ──POST /opiniao──▶ ia-opiniao ──▶ skills/ (Markdown versionado)
   (evidências do pregão)            ├──▶ conhecimento/ (fichas .md, leitura direta por metadado)
                                     ├──▶ vetores (RAG top-k filtrado por ativo/setor/data)
                                     ├──▶ ollama /api/chat (temperatura 0, format=json)
                                     └──▶ validador ──▶ resposta | reserva por regra
gerar-insights ◀── JSON validado ────┘ → grava opiniao_ia → gestor GET /ativos/{s}/opiniao → painel
```

### 4.3 Rede e implantação

- `ia-opiniao` expõe `8000` só na rede (sem porta no host, exceto em dev: `127.0.0.1`).
- **Duas redes (decisão de 2026-10-07):** `ia` (`internal: true`, sem saída para a internet) liga `ia-opiniao`, `ollama` e `vetores`, e é a única que o `gerar-insights` precisa para chamar o serviço. A leitura do MySQL (job de fichas, DEC-IA-05) usa a rede `observability` já existente, e **só o container do job** entra nela; o `ia-opiniao` que atende `/opiniao` não tem acesso ao banco (NFR-IA-06). O download de modelos é passo manual fora da rotina (`ollama pull` com a rede padrão, uma vez).
- `compose.ia.yml` e `compose.ia-gpu.yml` **passam a morar neste repositório** (posse transferida da infra, onde existiam desde 2026-10-07, TASK-IA-01); a infra remove os seus. Uso: `docker compose -f ../infra-b3-ecossytem/docker-compose-local.yml -f compose.ia.yml --profile ia up -d`. Porta do Ollama no host: `127.0.0.1:11435` (a 11434 costuma ser do Ollama instalado no Windows). GPU opcional via `compose.ia-gpu.yml`; neste PC o Docker não enxerga a GPU (WSL sem adaptadores), então o padrão é CPU.
- Imagem publicada como `ewertonmiranda/insider-ia-b3-ecossytem:develop` pelo CI, como os demais.

---

## 5. Contratos

### 5.1 `POST /opiniao` (CTR-IA-01)

Entrada:
```json
{ "simbolo": "PETR4", "data_pregao": "2026-10-06", "horizonte_pregoes": 21,
  "evidencias": [ { "id": "sinal_momentum", "rotulo": "Sinal técnico de momentum", "valor": "NEUTRO_TECNICO", "direcao": 0 } ],
  "permitidas": ["SINAL_NEUTRO", "SEM_BASE"], "risco_calculado": "RISCO_MEDIO",
  "motivo_sem_base": null, "dados_ausentes": ["..."],
  "versao_regra": "2026.09.27-3" }
```
`permitidas` (ordenadas da mais forte para a mais cautelosa) e `risco_calculado` são **entradas obrigatórias**: o `gerar-insights` continua dono das evidências, das opiniões permitidas e do risco (`app/opiniao/regras.py`); este serviço escolhe dentro do permitido, redige e valida, e é a base da reserva por regra. Sem esses dois campos o validador não tem contra o quê conferir (REQ-IA-03/04).
Saída:
```json
{ "opiniao": "SINAL_NEUTRO", "risco": "RISCO_MEDIO",
  "justificativa": [ { "evidencia_id": "sinal_momentum", "leitura": "..." }, { "trecho_id": "evidencia/momentum#2016-2026", "leitura": "..." } ],
  "o_que_invalida": ["..."], "dados_ausentes": ["..."], "fontes": ["conhecimento/evidencia/momentum.md#resultado"],
  "modelo": "qwen2.5:7b-instruct", "skills_versao": "skills@<hash>", "origem": "MODELO" }
```
`o_que_invalida` **não é escrito pelo modelo**: é calculado das evidências que apontam no sentido contrário da opinião (o 1.5B copiava ids e evidências nesse campo, observado em PETR4, 2026-10-06). A justificativa tem de 2 a 5 itens e só cita o que sustenta a opinião. Cada item de `justificativa` cita `evidencia_id` **ou** `trecho_id`.

Vocabulário fechado: `opiniao ∈ {SINAL_POSITIVO, SINAL_NEGATIVO, SINAL_NEUTRO, SEM_BASE}`, `risco ∈ {RISCO_BAIXO, RISCO_MEDIO, RISCO_ALTO}`, `origem ∈ {MODELO, REGRA}` — iguais aos `CHECK` da V22.

### 5.2 Demais endpoints

| Rota | Função |
|---|---|
| `POST /indexar` | (Re)indexa fichas e fundamentos alterados (por hash). Também disponível como job `python -m app.rag.indexar`. |
| `GET /skills` | Lista skills, versão e hash do conjunto. |
| `GET /saude` | Modelo carregado, tamanho do índice, versão das skills, data da última indexação. |

### 5.3 Persistência

- `opiniao_ia` continua gravada pelo `gerar-insights`. `versao_prompt` passa a registrar `skills@<hash>`.
- **Sem migration (DEC-IA-03):** os `trecho_id` usados vão dentro de `justificativa_json` (item com `trecho_id` em vez de `evidencia_id`) e na lista `fontes` da resposta. Nenhuma coluna nova; o gestor e o painel só precisam aceitar o item com `trecho_id` (TASK-IA-14).

### 5.4 Variáveis de ambiente

`OLLAMA_URL`, `MODELO_CHAT` (padrão `qwen2.5:0.5b-instruct` desde 2026-10-08; antes `qwen2.5:1.5b-instruct`), `MODELO_EMBED` (`nomic-embed-text`), `VETORES_URL`, `DIR_SKILLS`, `DIR_CONHECIMENTO`, `DB_*` (só leitura, para o gerador de fichas), `LOG_LEVEL`.

---

## 6. Conhecimento

### 6.1 Três camadas

| Camada | Formato | Conteúdo | Atualização |
|---|---|---|---|
| Skills | `skills/<nome>/SKILL.md` + apoio (`limites.yaml`, `schema.json`) | **Como ler**: regras, limites, vocabulário, formato | PR, raramente |
| Fichas | `conhecimento/**/*.md` com cabeçalho YAML, geradas por job | **Resultados pré-calculados** de anos fechados | anual / trimestral / semanal |
| RAG | Índice vetorial de trechos das fichas e fundamentos | **Busca** do trecho certo com fonte | ao mudar o hash de uma ficha |

O banco segue como fonte de verdade; as fichas são cópia condensada e imutável dos anos fechados.

### 6.2 Skills

```
skills/
  leitura-valuation/     Graham ajustado pela Selic, earnings yield, P/L vs faixa do setor
  leitura-tecnica/       MM20/MM50, momentum, reversão, z-score, volume relativo
  leitura-fatores/       percentis, direção esperada de cada fator (Plano LAC)
  leitura-eventos/       fato relevante, proventos, OPA/preço travado, desdobramento
  horizonte-curto/       21 pregões: pesos e evidências relevantes
  horizonte-medio/       63 pregões
  horizonte-longo/       126 pregões
  conformidade-cvm/      vocabulário neutro, aviso obrigatório, proibições
  formato-resposta/      schema.json do CTR-IA-01
```
- Seleção pelo orquestrador conforme horizonte e evidências presentes (só as relevantes entram no contexto).
- Cada skill tem `versao:` no cabeçalho; o conjunto ativo gera `skills@<hash>`.

### 6.3 Fichas pré-calculadas (anos fechados 2009–2025)

| Pasta | Uma ficha por | Conteúdo principal | Frequência |
|---|---|---|---|
| `conhecimento/ativos/` | papel líquido (~300) | Retorno, volatilidade, drawdown e recuperação por ano; beta; LPA, VPA, ROE, margem, dívida/EBITDA (DFP); proventos (DVA); P/L e Graham no fim de cada ano e retorno nos 12 meses seguintes; eventos (desdobramento, grupamento, OPA, troca de ticker); sazonalidade e reação a resultados | anual + trimestral (ITR) |
| `conhecimento/setores/` | setor (~40) | Faixas típicas de P/L, ROE, margem e dívida por ano; retorno vs mercado; anos de pico e vale do ciclo | anual |
| `conhecimento/mercado/` | ano + `regimes.md` | Retorno do mercado, Selic, IPCA, CDI, amplitude (altas x baixas), maiores ganhadores/perdedores; regimes (2015–16, 2020, 2022–24, ralis eleitorais 2018/2022/2026) | anual |
| `conhecimento/evidencia/` | regra/fator | Acerto e excesso por horizonte, período e setor, com intervalo de confiança; testes já feitos (ex.: momentum 20p ⇒ 49,1%); spread entre quintis dos fatores por regime | semanal |
| `conhecimento/fundamentos/` | tema | Graham, Piotroski, fatores, leitura de DFP/DVA, armadilhas (desdobramento sem ajuste, cíclicas, OPA) | manual |

Modelo de ficha:
```markdown
---
tipo: ativo
simbolo: PETR4
setor: Petróleo e Gás
cobertura: 2009-2025
disponivel_ate: 2026-03-31   # maior data_entrega usada (ponto no tempo)
gerado_em: 2026-10-07
fonte: [cotacao_b3_diaria, indicador_fundamentalista, provento_contabil, evento_corporativo]
hash: <sha256>
---
## Resumo            (até 5 linhas)
## Por ano           (tabela: ano, retorno, vol., drawdown, P/L fim, ROE, DY, retorno 12m seguintes)
## Eventos
## Padrões observados (sempre com n e período)
## Limitações        (obrigatória: dados ausentes, anos sem DFP, ajustes faltando)
```
Tamanho-alvo: 2–4 KB por ficha de ativo; acervo total na casa de poucos MB, versionado no Git.

### 6.4 Regras de ponto no tempo

- Ano corrente nunca entra em ficha; vem das evidências do dia.
- Cada linha carrega a data em que o dado ficou disponível (`data_entrega` da CVM). A busca só devolve trechos com disponibilidade ≤ `data_pregao` analisada — as mesmas fichas servem ao backtest sem vazamento.
- Preços sem ajuste de evento corporativo são marcados em "Limitações" até o ajuste do Plano LAC (`evento_corporativo`) estar aplicado.

### 6.5 Como o contexto é montado (barato)

1. Leitura direta por metadado (sem busca vetorial): resumo da ficha do ativo, faixa do setor, ficha de evidência das regras citadas.
2. Busca vetorial só para temas abertos/fundamentos: top-k 3–5, filtrada por `simbolo`, `setor`, `tipo` e disponibilidade.
3. Orçamento de contexto: 2–4 mil tokens; cada bloco com `trecho_id` para o validador.

---

## 7. Requisitos

### 7.1 Funcionais

| ID | Requisito | Status |
|---|---|---|
| REQ-IA-01 | `POST /opiniao` conforme CTR-IA-01, um horizonte por chamada | PLANEJADO |
| REQ-IA-02 | Seleção de skills por horizonte e evidências; hash do conjunto na resposta | PLANEJADO |
| REQ-IA-03 | Validador: vocabulário fechado, citações existentes, números presentes nas entradas, aviso de conformidade; falha ⇒ reserva por regra | PLANEJADO |
| REQ-IA-04 | Reserva por regra sempre disponível (porta de `app/opiniao/regras.py`) | PLANEJADO |
| REQ-IA-05 | Gerador de fichas `.md` (ativos, setores, mercado, evidência) idempotente por hash | PLANEJADO |
| REQ-IA-06 | Indexador do RAG incremental (só trechos com hash novo) | PLANEJADO |
| REQ-IA-07 | Busca com filtro de ponto no tempo e metadados | PLANEJADO |
| REQ-IA-08 | `GET /saude` e `GET /skills` | PLANEJADO |

### 7.2 Não funcionais

| ID | Requisito |
|---|---|
| NFR-IA-01 | Determinismo: temperatura 0, `format: json`, mesmas entradas ⇒ mesma saída (por versão de modelo e skills) |
| NFR-IA-02 | Latência por chamada (medida em 2026-10-07 neste PC, 4 núcleos, GPU de 2 GB): **~160 s** no container em CPU com 1.5b; **~28 s** no Ollama do Windows com GPU e 1.5b. Meta: p95 ≤ 45 s com GPU e 1.5b; em CPU o job roda em lote fora do horário (315 chamadas ≈ 14 h em CPU, ≈ 2,5 h com GPU), então a opinião do dia usa a reserva por regra até o lote terminar. O 7b (~4,7 GB quantizado) não cabe nos 2 GB de GPU |
| NFR-IA-03 | Sem rede externa em execução |
| NFR-IA-04 | Observabilidade: log estruturado com `simbolo`, `horizonte`, `skills_versao`, `modelo`, `origem`, motivo de reserva |
| NFR-IA-05 | Avaliação offline no CI: conjunto fixo de dossiês; mudança de skill/modelo não pode piorar as métricas |
| NFR-IA-06 | GETs sem efeito colateral; o serviço não grava no MySQL de negócio |

---

## 8. Decisões em aberto

| ID | Decisão | Opções / recomendação |
|---|---|---|
| DEC-IA-01 | Onde ficam as fichas | Git deste repo (recomendado: histórico e revisão) x volume Docker |
| DEC-IA-02 | Motor de vetores | SQLite + `sqlite-vec` no início (zero serviço extra); Qdrant quando passar de ~50 mil trechos |
| DEC-IA-03 | Gravar fontes usadas | **Decidido (2026-10-07): campo dentro de `justificativa_json`, sem V23.** Evita migration e disputa de número no hub; o painel já lê esse JSON |
| DEC-IA-04 | Modelo alvo | **Revisto (2026-10-08): `qwen2.5:0.5b-instruct`** — máquina sem GPU; em CPU o 1.5b gerava ~2,6 tokens/s e estourava o timeout em toda chamada (nenhuma resposta 200 em 72 h). Validador e reserva por regra compensam a fraqueza. Antes (2026-10-07): 1.5b. O 7b só com GPU (TASK-IA-13) |
| DEC-IA-05 | Quem gera as fichas | **Decidido (2026-10-07): job deste repo lendo o MySQL**, executado pela Sessão 03 (TASK-IA-07/08), com rede e usuário só de leitura |
| DEC-IA-06 | Provedor na nuvem | **Decidido (2026-10-08): Gemini (Google) é o provedor principal**, ordem `gemini → ollama → regra` no lote e no card. Só dados públicos de mercado saem para a nuvem (dossiê, fichas, manchetes); nada de carteira, preço médio ou dado pessoal. Revoga P-5 e NFR-IA-03 **apenas** para o `ia-opiniao` falando com a API do Gemini (seção 13) |
| DEC-IA-07 | Como o painel chega ao serviço | **Decidido (2026-10-08): proxy `/ia/*` no `server.js` do painel → `ia-opiniao:8000`**, sem passar pelo gestor (streaming simples, Java intocado). O painel entra na rede `ia` pelo override em `compose.ia.yml` |
| DEC-IA-08 | Chat sem Gemini | **Decidido (2026-10-08): chat fica indisponível** quando nenhum modelo Gemini responde (cota, pausa ou erro). O modelo local 0.5b **não** atende chat; continua só como reserva do lote/card |
| DEC-IA-09 | Chave da API | **Decidido (2026-10-08): `GEMINI_API_KEY` só em `.env.ia` na raiz deste repo (ignorado pelo `.gitignore`, padrão `.env.*`)**, lido pelo `compose.ia.yml`. Nunca em código, log, resposta, `/saude`, teste ou SPEC. Sem chave, o serviço sobe e trata o Gemini como indisponível |

---

## 9. Plano de execução (tarefas)

**Responsáveis (redistribuído pelo usuário em 2026-10-08; substitui a divisão de 2026-10-07):** Sessão 01 — TASK-IA-03; Sessão 02 — TASK-IA-04, 11 e 14 (e fechar o status de 02/05, que entregou em `8e16bf3`); Sessão 03 — TASK-IA-06, 09, 10, 12, 13 e o que faltar de 02/05. Ordem: IA-10 (Sessão 03) desbloqueia IA-11 (Sessão 02), que desbloqueia IA-14; IA-03 (Sessão 01) depende de IA-02. RAG (TASK-IA-10/11) deixa de estar adiado.

### Fase 1 — Extrair o serviço (sem mudar resultado)

| ID | Tarefa | Depende | Aceite | Status |
|---|---|---|---|---|
| TASK-IA-01 | Esqueleto do repo: FastAPI, Dockerfile, `compose.ia.yml` (duas redes, 4.3), CI (lint + testes + build); remover `compose.ia*.yml` da infra | — | `GET /saude` responde no compose local | IMPLEMENTADO (2026-10-07): `/saude` e `/skills` no ar no compose local (container `healthy`, modelo baixado detectado), rede `ia` sem internet conferida, CI só com testes. Falta remover `compose.ia*.yml` da infra |
| TASK-IA-02 | Portar `modelo_llm.py`, validador e reserva por regra de `gerar-insights/app/opiniao` (contrato com `permitidas` e `risco_calculado`, 5.1) | TASK-IA-01, TASK-IA-05 | Linhas `origem = REGRA` idênticas às do gerador atual nos 315 dossiês de 2026-10-06; linhas `MODELO` passam no mesmo validador | IMPLEMENTADO (2026-10-07, 8e16bf3): `POST /opiniao` com validador e reserva por regra; os 315 dossiês de 2026-10-06 reproduzem o esperado sem divergência (`tests/test_avaliacao.py`); linhas MODELO passam no mesmo validador. Sobrou, fora desta task: com o Ollama em CPU o limite de 180 s estoura e o serviço responde pela regra (ver IA-13/DEC-IA-04) |
| TASK-IA-03 | `gerar-insights` passa a chamar `POST /opiniao` por HTTP, enviando evidências, `permitidas` e `risco_calculado` | TASK-IA-02 | Linhas `REGRA` de `opiniao_ia` idênticas antes/depois (as de modelo dependem de semente e versão: só precisam passar no validador); prompt removido do worker | VERIFICADO (Sessão 01, 2026-10-08): gerar-insights `c885678` chama `POST /opiniao` (identidade por `GET /saude`; `versao_prompt = skills@hash`; reserva local se o serviço cai); prompt/validador/Ollama removidos do worker. Aceite: 315/315 linhas REGRA de 2026-10-06 idênticas (regra local = banco = reserva do serviço); ponta a ponta com WEGE3 gravou 3 linhas pelo serviço |

### Fase 2 — Skills

| ID | Tarefa | Depende | Aceite | Status |
|---|---|---|---|---|
| TASK-IA-04 | Converter o prompt atual em skills (seção 6.2) | TASK-IA-02 | Conjunto de avaliação não piora | IMPLEMENTADO (2026-10-08, c44b8f8): 9 skills em `skills/` selecionadas por horizonte e evidências, schema em `formato-resposta/schema.json`, testes verdes (`tests/test_skills.py`). A comparação de qualidade com o modelo contra o prompt embutido foi cancelada por decisão do usuário (priorizar entrega); `python -m avaliacao.rodar --provedor ollama [--sem-skills]` fica disponível para rodar depois. O caminho por regra não muda (315 dossiês sem divergência) |
| TASK-IA-05 | Conjunto de avaliação (`avaliacao/dossies`, `esperado`) e métrica no CI. Os dossiês saem de `opiniao_ia` (pregão 2026-10-06, `evidencias_json`, risco e permitidas recalculadas pelas regras) | TASK-IA-01 | CI falha em regressão | IMPLEMENTADO (2026-10-07, 8e16bf3): 315 dossiês e esperados em `avaliacao/`, exportados por `gerar-insights/app/opiniao/exportar_avaliacao.py`; `python -m avaliacao.rodar` (provedor `regra` ou `ollama`) e `tests/test_avaliacao.py` no CI falham em regressão |
| TASK-IA-06 | Corrigir falhas observadas: contradição sinal x evidência, ids de fator em "o que invalida", excesso de justificativas. **Já resolvidas no gerador atual** (prompt 1.2, 2026-10-07: justificativa só com o que sustenta a opinião, máx. 5, e `o_que_invalida` calculado das evidências contrárias); falta portar e cobrir com casos | TASK-IA-02 | Casos de PETR4/2026-10-06 passam no validador | PLANEJADO (Sessão 03, delegado em 2026-10-08) |

### Fase 3 — Fichas e RAG

| ID | Tarefa | Depende | Aceite | Status |
|---|---|---|---|---|
| TASK-IA-07 | Gerador das fichas de **evidência** e **setor** (maior valor, poucas consultas) — Sessão 03 | DEC-IA-05 (decidida) | Fichas geradas, hash estável em reexecução | IMPLEMENTADO (Sessão 03, 2026-10-07): `app/fichas/evidencia.py` e `setores.py`; 18 fichas de evidência (16 fatores, momentum 20p semanal, placar das regras) e 39 de setor; reexecução sem mudança de dado regrava 0 (hash estável); tests/fichas |
| TASK-IA-08 | Gerador das fichas de **ativos** e **mercado/regimes** — Sessão 03. Critério do universo: papéis com fator `LIQUIDEZ_63D` e fundamentos; o banco tem 2.116 códigos no COTAHIST e 221 CNPJs com DFP anual, então "~300" é o teto, não a meta | TASK-IA-07 | ≤ 4 KB por ficha, seção Limitações presente (inclui "eventos corporativos inferidos: 89 registros") | IMPLEMENTADO (Sessão 03, 2026-10-07): `app/fichas/ativos.py` e `mercado.py`; 243 fichas de ativo (LIQUIDEZ_63D + DFP anual; maior 3,7 KB), 17 anos de mercado + `regimes.md`; Limitações com os 89 eventos; ano corrente fora; `disponivel_ate` = maior entrega usada |
| TASK-IA-09 | Fundamentos a partir do glossário/fórmulas do painel e PDFs de estudo | — | Trechos com fonte e seção | PLANEJADO (Sessão 03, delegado em 2026-10-08) |
| TASK-IA-10 | Indexador incremental + busca com filtro de ponto no tempo | DEC-IA-02, TASK-IA-07 | Teste: trecho com disponibilidade futura nunca retorna | IMPLEMENTADO (Sessão 03, 2026-10-08): `app/rag/` (trechos, indice SQLite+FTS5, indexador incremental, busca com RRF textual+vetor); `disponivel_ate` por trecho (linha anual = coluna Disp. da ficha); 4.530 trechos, reindexação sem mudança regrava 0; teste de trecho futuro em tests/rag. Sem `nomic-embed-text` baixado, a busca é só textual |
| TASK-IA-11 | Orquestrador monta contexto (6.5) e cita `trecho_id` | TASK-IA-10 | Respostas citam fontes; validador confere | IMPLEMENTADO (2026-10-08): contexto com trechos via `app.rag` real (`ContextoRag`: leitura por metadado + busca textual, filtro de ponto no tempo), citação por `trecho_id` validada e `fontes` na resposta; verificado com o índice real (PETR4 em 2026-10-06 devolve 4 trechos) e `POST /indexar` indexando 4.530 trechos no container. Busca só textual até o nomic-embed-text ser baixado |
| TASK-IA-12 | Agendamento: anual (DFP), trimestral (ITR), semanal (evidência) na rotina da manhã | TASK-IA-08 | Registro em `etl_execucao` | EM ANDAMENTO (Sessão 03/feature-esqueleto, 2026-10-07) |

### Fase 4 — Modelo e painel

| ID | Tarefa | Depende | Aceite | Status |
|---|---|---|---|---|
| TASK-IA-13 | Trocar para 7b com GPU e comparar no conjunto de avaliação | TASK-IA-05, DEC-IA-04 | Métrica igual ou melhor; latência dentro de NFR-IA-02 | PLANEJADO (Sessão 03, delegado em 2026-10-08) |
| TASK-IA-14 | Gestor e painel: aceitar item de `justificativa_json` com `trecho_id` e mostrar fontes no cartão "Opinião por horizonte" — Sessão 01 | DEC-IA-03 (decidida), TASK-IA-11 | Cada justificativa com link para a ficha/trecho | IMPLEMENTADO (Sessão 01 a pedido da Sessão 02, 2026-10-08): worker grava o item inteiro (`c885678`), gestor devolve `fonte`/`trecho` (`8a2cc22`), cartão mostra "fonte: <caminho>" e o trecho num expansível escapado (`7d8874d`) |

---

## 10. Estrutura do repositório (alvo)

```
insider-ia-b3-ecossytem/
  app/
    api.py              FastAPI: /opiniao, /indexar, /skills, /saude
    orquestrador.py     seleção de skills + contexto + chamada + validação
    skills.py           carga e hash das skills
    validador.py        vocabulário, citações, números, conformidade
    regras.py           reserva por regra
    provedores/ollama.py
    rag/ indexador.py  busca.py
    conhecimento/ gerar_fichas.py  consultas.sql
  skills/               (seção 6.2)
  conhecimento/         ativos/ setores/ mercado/ evidencia/ fundamentos/
  avaliacao/            dossies/*.json  esperado/*.json
  tests/
  compose.ia.yml  compose.ia-gpu.yml  Dockerfile  requirements.txt
  SPEC.md  README.md
```

## 11. Verificação

- `pytest -q` e `ruff check app tests`.
- `docker compose -f ../infra-b3-ecossytem/docker-compose-local.yml -f compose.ia.yml --profile ia up -d` e, com `exec ia-opiniao python -c "import urllib.request;print(urllib.request.urlopen('http://127.0.0.1:8000/saude').read().decode())"`, conferir `/saude` (a rede `ia` é interna e não publica porta no host).
- Avaliação: `python -m avaliacao.rodar` compara com `esperado/` e imprime acerto de formato, taxa de reserva por regra e citações inválidas.

## 12. Aviso regulatório

Toda saída é leitura automática de números, **regra experimental**, e **não é recomendação de investimento** (Res. CVM 20/2021). O vocabulário é neutro (`SINAL_*`), e o painel mostra sempre o aviso e o selo "Experimental".

---

## 13. Plano de 2026-10-08 — Gemini, cota, lote gradual, chat e card IA

**Status:** PLANEJADO · **Decisões:** DEC-IA-06..09 (seção 8) · **Coordenação:** hub `infra-b3-ecossytem/SPEC.md` 1A.4, linhas `GEM-*`.

### 13.1 Divisão por repositório (execução paralela sem colisão)

Cada grupo de agentes (Codex/Claude) trabalha **só no seu repositório**. A integração acontece pelos contratos da 13.3, que são a fonte da verdade: enquanto o outro lado não está pronto, cada grupo testa com dublês/fixtures do contrato.

| Grupo | Repositório | Tarefas | Arquivos que só ele toca |
|---|---|---|---|
| A | `insider-ia-b3-ecossytem` (este) | TASK-IA-24..39 | `app/**`, `tests/**`, `compose.ia.yml` (inclusive os overrides de `gerar-insights` e `painel-ativos-frontend`), `requirements.txt`, `.env.example`, este SPEC |
| B | `gerar-insights` | TASK-GEM-L1..L4 (SPEC do gerar-insights) | `app/opiniao/**`, `tests/opiniao/**`, `app/config/settings.py` (só as chaves novas) |
| C | `painel-ativos-frontend` | TASK-NOT-1..6 e TASK-CHAT-1..7 (SPEC do painel) | `server.js`, `proxy/**`, `public/**`, `tests/**` |
| — | `infra-b3-ecossytem` | só o hub (linhas `GEM-*`, contratos em 1A.5, diário 1A.7) | nada de código |
| — | `gestor-ativos-brutos` | nenhuma mudança | — |

Regras anticolisão:
1. Mudou contrato? Só o **grupo A** edita a 13.3; quem consome abre uma linha no hub pedindo a mudança e espera o commit do SPEC.
2. Nenhum grupo edita arquivo de outro repositório, nem para "ajustar um detalhe".
3. Cada tarefa abaixo lista os arquivos que cria/altera; dois agentes do mesmo grupo não pegam tarefas que tocam o mesmo arquivo ao mesmo tempo (ver coluna **Arquivos**).

### 13.2 Fluxo

```
            ┌───────────────────── ia-opiniao (FastAPI) ─────────────────────┐
worker ───▶ │ POST /opiniao/ativo (uso=lote)                                  │
painel ───▶ │ GET  /ativo/{s}           POST /ativo/{s}/leitura   (uso=card)  │
painel ───▶ │ POST /chat  (SSE, uso=chat)                                     │
            │   └─▶ Governador de cota (SQLite em /app/var/cota.sqlite)      │
            │        └─▶ Cadeia: Gemini[m1, m2, …] → Ollama 0.5b → regra     │
            │             (chat: só Gemini; sem Gemini ⇒ indisponível)        │
            └─────────────────────────────────────────────────────────────────┘
redes: `ia` (internal: ollama, worker, painel)  +  `saida` (só ia-opiniao → API do Gemini)
```

### 13.3 Contratos (fonte da verdade para os grupos B e C)

Rotas do serviço sem prefixo. **O painel chama tudo com o prefixo `/ia` e o proxy dele remove o prefixo** (DEC-IA-07, TASK-CHAT-1 do painel): `/ia/chat` → `/chat`, `/ia/ativo/WEGE3` → `/ativo/WEGE3`, `/ia/manchetes/resumo` → `/manchetes/resumo`, `/ia/saude` → `/saude`. O worker chama direto (`IA_URL`), sem prefixo. O painel **não** usa `/opiniao` nem `/opiniao/ativo` (quem gera opinião é só o worker; TASK-IA-37 descartada).

**CTR-IA-01 v1.1 — `POST /opiniao/ativo`** (os 3 horizontes numa chamada; `POST /opiniao` v1.0 continua igual e aceito)

Entrada:
```json
{ "simbolo": "WEGE3", "data_pregao": "2026-10-07", "uso": "lote",
  "dados_ausentes": ["..."], "versao_regra": "2026.09.27-3",
  "horizontes": [
    { "horizonte_pregoes": 21,
      "evidencias": [ { "id": "sinal_momentum", "rotulo": "...", "valor": "NEUTRO_TECNICO", "direcao": 0 } ],
      "permitidas": ["SINAL_NEUTRO", "SEM_BASE"], "risco_calculado": "RISCO_MEDIO", "motivo_sem_base": null },
    { "horizonte_pregoes": 63, "...": "..." },
    { "horizonte_pregoes": 126, "...": "..." } ] }
```
- `uso`: hoje só `lote` (padrão); define o balde de cota (13.4). Outros valores ⇒ 422.
- Cada item de `horizontes` tem os mesmos campos e regras do CTR-IA-01 v1.0.

Saída (HTTP 200 sempre que o corpo for válido; 422 só para corpo inválido):
```json
{ "simbolo": "WEGE3", "data_pregao": "2026-10-07",
  "modelo": "gemini-<nome>", "skills_versao": "skills@<hash>",
  "itens": [ { "horizonte_pregoes": 21, "opiniao": "...", "risco": "...", "justificativa": [ ... ],
               "o_que_invalida": [ ... ], "dados_ausentes": [ ... ], "fontes": [ ... ],
               "origem": "MODELO", "modelo": "gemini-<nome>", "tentativas": 1 } ],
  "cota": { "balde": "lote", "restante_hoje": 37, "gemini_disponivel": true } }
```
- Cada item segue a saída v1.0. O `modelo` de cada item diz quem respondeu (Gemini, Ollama ou `regra`).
- Uma resposta só do modelo para os 3 horizontes; o validador roda **por item**. Item rejeitado cai para o próximo provedor **só para aquele item**.
- `cota.gemini_disponivel = false` avisa o worker que o restante do lote do dia não deve mais chamar o serviço (TASK-GEM-L3).

**CTR-IA-02 — `POST /chat`** (Server-Sent Events, `Content-Type: text/event-stream`)

Entrada:
```json
{ "sessao_id": "uuid-v4 gerado pelo painel", "mensagem": "texto (1..1000 caracteres)", "simbolo": "WEGE3 | null" }
```
Eventos, nesta ordem:
| Evento | `data` (JSON) | Quando |
|---|---|---|
| `inicio` | `{"modelo": "gemini-<nome>", "sessao_id": "..."}` | Primeiro evento, quando um Gemini aceitou a chamada |
| `token` | `{"texto": "pedaço"}` | 0..n vezes |
| `fontes` | `{"fontes": [{"tipo": "ficha\|comunicado\|noticia\|pregao", "rotulo": "...", "ref": "..."}]}` | 0..1 vez, antes de `fim` |
| `aviso` | `{"texto": "número sem fonte: 12,4%"}` | 0..n vezes (validação leve, 13.6) |
| `fim` | `{"tokens_saida": 123, "restante_hoje": 41}` | Último em caso de sucesso |
| `erro` | `{"codigo": "INDISPONIVEL\|LIMITE\|FORA_DO_TEMA\|ENTRADA_INVALIDA", "mensagem": "texto para o usuário", "tentar_apos": "2026-10-08T15:00:00-03:00 \| null"}` | Último em caso de falha |

- `INDISPONIVEL`: nenhum Gemini respondeu (DEC-IA-08). `LIMITE`: limite por sessão ou cota do balde `chat`. `FORA_DO_TEMA`: pergunta fora de mercado/finanças/B3.
- O texto de `token` é **texto puro**: o painel nunca o interpreta como HTML.

**CTR-IA-03 — `GET /ativo/{simbolo}`** (só leitura, sem cota, cache por pregão)
```json
{ "simbolo": "WEGE3", "data_pregao": "2026-10-07",
  "cotacao": { "fechamento": 52.1, "variacao_1d": 0.012, "variacao_1m": -0.03, "variacao_12m": 0.18 },
  "fundamentos": { "pl": 28.4, "roe": 0.31, "divida_liquida_ebitda": -0.2 },
  "sinais": [ { "id": "...", "rotulo": "...", "valor": "...", "direcao": 1 } ],
  "opiniao": [ { "horizonte_pregoes": 21, "opiniao": "...", "risco": "...", "origem": "MODELO" } ],
  "comunicados": [ { "data": "2026-10-03", "titulo": "...", "link": "..." } ],
  "manchetes": [ { "titulo": "...", "link": "...", "fonte": "...", "publicadoEm": "..." } ],
  "aviso": "Leitura automática dos números, regra experimental. Não é recomendação de investimento." }
```
- Campo sem dado vem `null` (nunca 0). `sinais` no máximo 3 (os de maior |direção| do dia). `comunicados` ≤ 3, `manchetes` ≤ 5.
- Fonte: **GETs já existentes do gestor** (o `ia-opiniao` continua sem acesso ao MySQL, NFR-IA-06): `/ativos/robusto/{s}` (cotação), `/ativos/{s}/pregoes` (variações 1m/12m), `/analises/{s}/fundamentos`, `/ativos/{s}/opiniao`, `/empresas/{s}/comunicados`; e RSS do Google News (mesma busca do painel). O gestor entra na rede `ia` pelo override do `compose.ia.yml` (nenhuma mudança no repo do gestor). 404 se o gestor não conhecer o símbolo.

**CTR-IA-04 — `POST /ativo/{simbolo}/leitura`** (uso `card`)
- Saída: `{ "simbolo": "...", "data_pregao": "...", "texto": "3 a 4 frases", "modelo": "...", "origem": "MODELO|REGRA", "gerado_em": "...", "em_cache": true }`.
- Cache por (símbolo, pregão): a segunda chamada no mesmo pregão não gasta cota.
- Sem Gemini/cota: `origem = REGRA` e `texto` montado por modelo de frase fixo a partir do CTR-IA-03.

**`GET /saude`** ganha o bloco (sem nunca expor a chave):
```json
"provedores": { "ordem_lote": ["gemini", "ollama"], "ordem_chat": ["gemini"],
  "gemini": { "configurado": true, "modelos": [ { "nome": "...", "em_pausa_ate": null, "usadas_hoje": 12, "teto_dia": 200 } ] } },
"cota": { "chat": { "restante_hoje": 41 }, "card": { "restante_hoje": 20 }, "lote": { "restante_hoje": 37 } }
```

### 13.4 Governador de cota

- **Baldes diários** (percentual do teto diário somado dos modelos Gemini): `chat` 40%, `card` 20%, `lote` 40% (variáveis `COTA_*_PCT`). Depois das 18h (America/Sao_Paulo) a sobra de um balde pode ser usada por outro.
- **Por modelo:** limite por minuto (`GEMINI_RPM`), teto diário (`GEMINI_RPD`), contados em SQLite (`/app/var/cota.sqlite`, volume `ia_indice` já existente). O dia zera à meia-noite de America/Los_Angeles (horário em que a cota do Google zera).
- **Pausa após 429:** usa o `retryDelay` da resposta; sem ele, 60 s; se a mensagem indicar cota diária, até o próximo zeramento.
- **Prioridade:** chat > card > lote. Com menos de 15% do teto do dia restante, o balde `lote` deixa de usar Gemini.
- **Cache de resposta:** chave = hash(provedor, modelo, prompt normalizado, schema); validade até o fim do dia. Repetição idêntica não gasta cota.

### 13.5 Variáveis novas

| Variável | Padrão | Observação |
|---|---|---|
| `GEMINI_API_KEY` | (vazia) | Só em `.env.ia` (DEC-IA-09). Vazia ⇒ Gemini indisponível |
| `GEMINI_MODELOS` | `gemini-3.8-flash` | Lista separada por vírgula, na ordem de tentativa. Os nomes válidos são os liberados para a chave no AI Studio |
| `GEMINI_RPM` / `GEMINI_RPD` | `10` / `200` | Por modelo; ajustar ao limite real da chave |
| `GEMINI_TIMEOUT_S` | `30` | Por chamada |
| `PROVEDORES_LOTE` | `gemini,ollama` | Ordem do lote e do card (DEC-IA-06) |
| `PROVEDORES_CHAT` | `gemini` | DEC-IA-08: sem `ollama` |
| `COTA_CHAT_PCT` / `COTA_CARD_PCT` / `COTA_LOTE_PCT` | `40` / `20` / `40` | Soma 100 |
| `CHAT_MAX_DIA_SESSAO` / `CHAT_INTERVALO_S` | `60` / `3` | Limite por sessão |
| `TIMEOUT_MODELO_S` | `90` | Ollama (antes 180), para caber no tempo do worker |
| `GESTOR_URL` | `http://gestor-ativos-brutos:8091` | Só GETs, para o CTR-IA-03 e as ferramentas do chat |

### 13.6 Tarefas — grupo A (este repositório)

Fase GEM-1 (base; desbloqueia tudo):

| ID | Tarefa | Arquivos | Depende | Aceite | Status |
|---|---|---|---|---|---|
| TASK-IA-24 | Provedor Gemini: `gerar(sistema, usuario, schema) -> str` (JSON com schema) e `conversar(mensagens, sistema) -> Iterator[str]` (streaming), SDK `google-genai`. 429 vira `ErroDeCota(espera_s, diaria: bool)`; 5xx/timeout/rede viram `ErroDoProvedor` | `app/provedores/gemini.py`, `requirements.txt`, `tests/test_gemini.py` | DEC-IA-06/09 | Testes com cliente falso: 429 com e sem `retryDelay`, 500, timeout, JSON pedido via schema; a chave nunca aparece em mensagem de erro | PLANEJADO |
| TASK-IA-25 | Governador de cota (13.4): baldes, RPM, RPD, pausa, prioridade, cache, relógio injetável | `app/cota.py`, `tests/test_cota.py` | — | Testes com relógio falso: zeramento em America/Los_Angeles, pausa de 429, teto por balde, sobra após 18h, corte do lote abaixo de 15%, cache impede segunda cobrança | PLANEJADO |
| TASK-IA-26 | Cadeia de provedores: percorre `PROVEDORES_*`, consulta o governador antes de cada chamada, valida cada resposta e passa ao próximo se rejeitada; Gemini sem segunda tentativa, Ollama mantém a sua. Log com provedor que respondeu e motivo de cada falha | `app/provedores/cadeia.py`, `app/orquestrador.py`, `tests/test_cadeia.py` | IA-24, IA-25 | 429 no m1 ⇒ m2; todos em pausa ⇒ Ollama; tudo falhou ⇒ regra; o `modelo` da resposta é o de quem respondeu; `POST /opiniao` v1.0 continua passando nos 315 dossiês (`tests/test_avaliacao.py`) | IMPLEMENTADO (Sessão 01, 2026-10-08): `app/provedores/cadeia.py` (`Cadeia`, `Elo`, `ErroDeCota`, porta `Governador` com `SemGovernador` até a IA-25, `montar_cadeia` por `PROVEDORES_LOTE/CHAT` com um elo por modelo de `GEMINI_MODELOS` quando o `GeminiProvedor` da IA-24 existir); `/opiniao` e `/opiniao/ativo` usam a cadeia (v1.1: item pendente segue sozinho ao próximo elo). Conferido com provedores falsos (429 → próximo; rejeitado → próximo; local refaz). Testes adiados por decisão do usuário |
| TASK-IA-27 | Configuração e compose: variáveis da 13.5 em `app/config.py`; `compose.ia.yml` com `env_file` `${IA_CONTEXT:-../insider-ia-b3-ecossytem}/.env.ia` (`required: false`), `ia-opiniao` nas redes `ia` + `saida`, override do `painel-ativos-frontend` (rede `ia`, `IA_URL=http://ia-opiniao:8000`) e do `gestor-ativos-brutos` (rede `ia`, para os GETs do CTR-IA-03); `.env.example` com as variáveis **sem valores**; `/saude` com o bloco da 13.3 | `app/config.py`, `app/api.py`, `compose.ia.yml`, `.env.example`, `tests/test_api.py` | IA-25 | `/saude` mostra provedores e cota e **não** contém a chave (teste); sem `.env.ia` o serviço sobe com Gemini indisponível | PLANEJADO |
| TASK-IA-28 | Teste de vazamento da chave: captura de log de todos os caminhos (sucesso, 429, erro, chat) com uma chave falsa; nenhuma ocorrência no texto capturado nem nas respostas | `tests/test_segredo.py` | IA-24..27 | Teste verde no CI | PLANEJADO |

Fase GEM-2 (lote gradual):

| ID | Tarefa | Arquivos | Depende | Aceite | Status |
|---|---|---|---|---|---|
| TASK-IA-29 | `POST /opiniao/ativo` (CTR-IA-01 v1.1): uma chamada ao modelo para os 3 horizontes, schema com `itens[]`, validação por item, item rejeitado vai ao próximo provedor sozinho; bloco `cota` na saída | `app/api.py`, `app/modelos.py`, `app/orquestrador.py`, `app/prompt.py`, `skills/formato-resposta/schema_ativo.json`, `tests/test_opiniao_ativo.py` | IA-26 | Com provedor falso: 1 chamada para 3 horizontes; item inválido isolado; `uso` escolhe o balde; v1.0 inalterada | IMPLEMENTADO (Sessão 01, 2026-10-08): `POST /opiniao/ativo` em `app/api.py`, `opinar_ativo` em `app/orquestrador.py`, modelos v1.1 em `app/modelos.py`, `schema_do_ativo`/`montar_mensagem_ativo` em `app/prompt.py` (schema derivado do da skill, sem arquivo novo). Item rejeitado ou ausente vai para a regra (a cadeia da IA-26 entra antes quando existir); `cota` fixa `gemini_disponivel=false` até a IA-25. Testes adiados por decisão do usuário |

Fase GEM-4 (chat):

| ID | Tarefa | Arquivos | Depende | Aceite | Status |
|---|---|---|---|---|---|
| TASK-IA-30 | `POST /chat` com SSE conforme CTR-IA-02; só `PROVEDORES_CHAT`; sem Gemini ⇒ `erro INDISPONIVEL` com `tentar_apos` | `app/chat/api.py`, `app/chat/sse.py`, `tests/chat/test_sse.py` | IA-26 | Ordem de eventos `inicio → token* → fontes? → aviso* → fim`, ou `erro`; teste do caso sem Gemini | PLANEJADO |
| TASK-IA-31 | Sessões: últimas 12 mensagens em SQLite, expiram em 24h; a cada 8 mensagens o histórico antigo vira um resumo (uma chamada no balde `chat`) | `app/chat/sessoes.py`, `tests/chat/test_sessoes.py` | IA-30 | Expiração e resumo testados com relógio e provedor falsos | PLANEJADO |
| TASK-IA-32 | Contexto do chat: trechos do RAG pela pergunta (`app.rag`) + pacote do ativo (CTR-IA-03) quando há `simbolo`; nada com data posterior ao pregão (P-4) | `app/chat/contexto.py`, `tests/chat/test_contexto.py` | IA-30, IA-35 | Pergunta sobre PETR4 traz ficha e pacote; filtro de ponto no tempo testado | PLANEJADO |
| TASK-IA-33 | Ferramentas só leitura que o Gemini pode chamar (function calling): `cotacao(s)`, `fundamentos(s)`, `opiniao(s)`, `comunicados(s)`, `comparar(s1, s2)`; cada uma é um GET fixo no gestor (lista do CTR-IA-03), com símbolo validado (`^[A-Z]{4}[0-9]{1,2}$`), no máximo 4 chamadas por mensagem e resposta truncada a 4 KB. O modelo nunca monta URL nem SQL. "Maiores altas do período" fica **fora** deste plano: exige endpoint novo no gestor | `app/chat/ferramentas.py`, `tests/chat/test_ferramentas.py` | IA-30, IA-35 | Símbolo inválido rejeitado sem chamar o gestor; 5ª chamada na mesma mensagem recusada; gestor fora ⇒ ferramenta devolve "dado indisponível" e o chat segue | PLANEJADO |
| TASK-IA-34 | Guardas do chat: prompt de sistema proíbe recomendação pessoal (responde com leitura dos sinais + aviso); classificador simples de tema (palavras e RAG) para `FORA_DO_TEMA`; número sem fonte vira evento `aviso`; vocabulário proibido ⇒ uma regeneração; limite por sessão (`CHAT_*`) | `app/chat/guardas.py`, `skills/chat/sistema.md`, `tests/chat/test_guardas.py` | IA-30 | Casos: "devo comprar X?", "receita de bolo", número inventado, 61ª mensagem do dia, 2 mensagens em 1 s | PLANEJADO |

Fase GEM-5 (card IA):

| ID | Tarefa | Arquivos | Depende | Aceite | Status |
|---|---|---|---|---|---|
| TASK-IA-35 | `GET /ativo/{s}` (CTR-IA-03): monta o pacote com os GETs do gestor + RSS de manchetes; cache por pregão; `null` para ausente; cliente do gestor reutilizado pelas ferramentas do chat | `app/ativo/pacote.py`, `app/ativo/cliente_gestor.py`, `app/ativo/noticias.py`, `tests/ativo/test_pacote.py` | IA-27 | Com gestor falso (servidor HTTP local nos testes): campos ausentes `null`, ≤3 sinais, ≤3 comunicados, ≤5 manchetes; 404 do gestor ⇒ 404; gestor fora ⇒ 503 com mensagem; GET sem efeito colateral (NFR-IA-06) | PLANEJADO |
| TASK-IA-36 | `POST /ativo/{s}/leitura` (CTR-IA-04): parágrafo de 3–4 frases, cache por (símbolo, pregão), números validados contra o pacote, reserva por frase fixa | `app/ativo/leitura.py`, `tests/ativo/test_leitura.py` | IA-26, IA-35 | Segunda chamada no mesmo pregão: `em_cache=true` e nenhuma cobrança; sem Gemini ⇒ `origem=REGRA` | PLANEJADO |
| TASK-IA-37 | (Descartada no desenho, 2026-10-08) Opinião sob demanda pelo painel: o painel não tem o dossiê (evidências, permitidas, risco), que é do worker. Ativo sem opinião do modelo mostra a da regra e a leitura da TASK-IA-36; favoritos entram na fila do lote seguinte (TASK-GEM-L2/L3 do gerar-insights) | — | — | — | DESCARTADA |

Fase GEM-6 (resumo de manchetes):

| ID | Tarefa | Arquivos | Depende | Aceite | Status |
|---|---|---|---|---|---|
| TASK-IA-38 | `POST /manchetes/resumo`: entrada `{ "manchetes": [{titulo, link, fonte, simbolos[]}] }` (≤30); saída `{ "topicos": [{ "texto": "...", "links": ["..."] }] }` com 3 tópicos, cada um citando ≥1 link da entrada; cache diário pelo hash da entrada; balde `card` | `app/manchetes/resumo.py`, `tests/test_resumo_manchetes.py` | IA-26 | Link citado fora da entrada ⇒ rejeitado; segunda chamada do dia não gasta cota | PLANEJADO |
| TASK-IA-39 | SPEC e README: marcar DEC-IA-06..09 aplicadas, atualizar 4.3 (rede `saida` no `ia-opiniao`), 5.2 (rotas novas) e NFR-IA-02 (latência com Gemini) depois de medir no ambiente real | `SPEC.md`, `README.md` | IA-24..38 | Seções coerentes com o código | PLANEJADO |

### 13.7 Aceite do plano (ponta a ponta, depois das imagens no Hub)

1. `/saude` lista Gemini configurado e cota; sem `.env.ia`, Gemini aparece não configurado e o lote cai em Ollama/regra.
2. Uma noite de lote grava em `opiniao_ia` linhas `origem=MODELO` com `modelo=gemini-*` para os ativos priorizados, sem nenhum 429 sequencial no log.
3. No painel: chat responde em streaming com fontes; sem Gemini mostra "Assistente indisponível até HH:MM".
4. Card IA da ficha mostra pacote, leitura e chat fixado no ativo; tela inicial mostra manchetes dos favoritos.
5. `grep` da chave nos logs de todos os containers e nas respostas: zero ocorrências.
