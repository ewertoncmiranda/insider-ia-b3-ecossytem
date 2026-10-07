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

- Rede Docker interna do compose local; `ia-opiniao` expõe `8000` só na rede (sem porta no host, exceto em dev: `127.0.0.1`).
- Containers sem saída para a internet (rede `internal: true` para `ia-opiniao`, `ollama`, `vetores`). O download de modelos é passo manual fora da rotina.
- `compose.ia.yml` deste repositório é incluído pela infra (`docker compose -f docker-compose-local.yml -f ../insider-ia-b3-ecossytem/compose.ia.yml --profile ia`). GPU opcional via `compose.ia-gpu.yml`.
- Imagem publicada como `ewertonmiranda/insider-ia-b3-ecossytem:develop` pelo CI, como os demais.

---

## 5. Contratos

### 5.1 `POST /opiniao` (CTR-IA-01)

Entrada:
```json
{ "simbolo": "PETR4", "data_pregao": "2026-10-06", "horizonte_pregoes": 21,
  "evidencias": [ { "id": "sinal_momentum", "rotulo": "Sinal técnico de momentum", "valor": "NEUTRO_TECNICO", "direcao": 0 } ],
  "versao_regra": "2026.09.27-3" }
```
Saída:
```json
{ "opiniao": "SINAL_NEUTRO", "risco": "RISCO_MEDIO",
  "justificativa": [ { "evidencia_id": "sinal_momentum", "leitura": "..." }, { "trecho_id": "evidencia/momentum#2016-2026", "leitura": "..." } ],
  "o_que_invalida": ["..."], "dados_ausentes": ["..."], "fontes": ["conhecimento/evidencia/momentum.md#resultado"],
  "modelo": "qwen2.5:7b-instruct", "skills_versao": "skills@<hash>", "origem": "MODELO" }
```
Vocabulário fechado: `opiniao ∈ {SINAL_POSITIVO, SINAL_NEGATIVO, SINAL_NEUTRO, SEM_BASE}`, `risco ∈ {RISCO_BAIXO, RISCO_MEDIO, RISCO_ALTO}`, `origem ∈ {MODELO, REGRA}` — iguais aos `CHECK` da V22.

### 5.2 Demais endpoints

| Rota | Função |
|---|---|
| `POST /indexar` | (Re)indexa fichas e fundamentos alterados (por hash). Também disponível como job `python -m app.rag.indexar`. |
| `GET /skills` | Lista skills, versão e hash do conjunto. |
| `GET /saude` | Modelo carregado, tamanho do índice, versão das skills, data da última indexação. |

### 5.3 Persistência

- `opiniao_ia` continua gravada pelo `gerar-insights`. `versao_prompt` passa a registrar `skills@<hash>`.
- Nova coluna sugerida para a infra (V23, decisão DEC-IA-03): `fontes_json` com os `trecho_id` usados.

### 5.4 Variáveis de ambiente

`OLLAMA_URL`, `MODELO_CHAT` (padrão `qwen2.5:1.5b-instruct`, alvo `qwen2.5:7b-instruct`), `MODELO_EMBED` (`nomic-embed-text`), `VETORES_URL`, `DIR_SKILLS`, `DIR_CONHECIMENTO`, `DB_*` (só leitura, para o gerador de fichas), `LOG_LEVEL`.

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
| NFR-IA-02 | Latência p95 ≤ 20 s por chamada em CPU com modelo 1.5b; ≤ 5 s com GPU e 7b |
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
| DEC-IA-03 | Gravar fontes usadas | Nova coluna `fontes_json` em `opiniao_ia` (V23 na infra) x campo dentro de `justificativa_json` |
| DEC-IA-04 | Modelo alvo | `qwen2.5:7b-instruct` com GPU; manter 1.5b como mínimo em CPU |
| DEC-IA-05 | Quem gera as fichas | Job deste repo lendo o MySQL (recomendado) x job no `gerar-insights` |

---

## 9. Plano de execução (tarefas)

### Fase 1 — Extrair o serviço (sem mudar resultado)

| ID | Tarefa | Depende | Aceite | Status |
|---|---|---|---|---|
| TASK-IA-01 | Esqueleto do repo: FastAPI, Dockerfile, `compose.ia.yml`, CI (lint + testes + build) | — | `GET /saude` responde no compose local | PLANEJADO |
| TASK-IA-02 | Portar `modelo_llm.py`, validador e reserva por regra de `gerar-insights/app/opiniao` | combinar com a Sessão 02 | Mesmas saídas do gerador atual para o pregão 2026-10-06 (315 dossiês) | PLANEJADO |
| TASK-IA-03 | `gerar-insights` passa a chamar `POST /opiniao` por HTTP | TASK-IA-02 | `opiniao_ia` idêntica antes/depois; prompt removido do worker | PLANEJADO |

### Fase 2 — Skills

| ID | Tarefa | Depende | Aceite | Status |
|---|---|---|---|---|
| TASK-IA-04 | Converter o prompt atual em skills (seção 6.2) | TASK-IA-02 | Conjunto de avaliação não piora | PLANEJADO |
| TASK-IA-05 | Conjunto de avaliação (`avaliacao/dossies`, `esperado`) e métrica no CI | TASK-IA-01 | CI falha em regressão | PLANEJADO |
| TASK-IA-06 | Corrigir falhas observadas: contradição sinal x evidência, ids de fator em "o que invalida", excesso de justificativas | TASK-IA-04 | Casos de PETR4/2026-10-06 passam no validador | PLANEJADO |

### Fase 3 — Fichas e RAG

| ID | Tarefa | Depende | Aceite | Status |
|---|---|---|---|---|
| TASK-IA-07 | Gerador das fichas de **evidência** e **setor** (maior valor, poucas consultas) | DEC-IA-05 | Fichas geradas, hash estável em reexecução | PLANEJADO |
| TASK-IA-08 | Gerador das fichas de **ativos** e **mercado/regimes** | TASK-IA-07 | ~300 ativos, ≤ 4 KB cada, seção Limitações presente | PLANEJADO |
| TASK-IA-09 | Fundamentos a partir do glossário/fórmulas do painel e PDFs de estudo | — | Trechos com fonte e seção | PLANEJADO |
| TASK-IA-10 | Indexador incremental + busca com filtro de ponto no tempo | DEC-IA-02, TASK-IA-07 | Teste: trecho com disponibilidade futura nunca retorna | PLANEJADO |
| TASK-IA-11 | Orquestrador monta contexto (6.5) e cita `trecho_id` | TASK-IA-10 | Respostas citam fontes; validador confere | PLANEJADO |
| TASK-IA-12 | Agendamento: anual (DFP), trimestral (ITR), semanal (evidência) na rotina da manhã | TASK-IA-08 | Registro em `etl_execucao` | PLANEJADO |

### Fase 4 — Modelo e painel

| ID | Tarefa | Depende | Aceite | Status |
|---|---|---|---|---|
| TASK-IA-13 | Trocar para 7b com GPU e comparar no conjunto de avaliação | TASK-IA-05, DEC-IA-04 | Métrica igual ou melhor; latência dentro de NFR-IA-02 | PLANEJADO |
| TASK-IA-14 | Painel: mostrar fontes citadas no cartão "Opinião por horizonte" | DEC-IA-03 | Cada justificativa com link para a ficha/trecho | PLANEJADO |

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
- `docker compose -f ../infra-b3-ecossytem/docker-compose-local.yml -f compose.ia.yml --profile ia up -d` e `curl http://localhost:8000/saude` (dev).
- Avaliação: `python -m avaliacao.rodar` compara com `esperado/` e imprime acerto de formato, taxa de reserva por regra e citações inválidas.

## 12. Aviso regulatório

Toda saída é leitura automática de números, **regra experimental**, e **não é recomendação de investimento** (Res. CVM 20/2021). O vocabulário é neutro (`SINAL_*`), e o painel mostra sempre o aviso e o selo "Experimental".
