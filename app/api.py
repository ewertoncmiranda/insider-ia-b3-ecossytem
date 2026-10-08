"""API do servico de IA (SPEC 5). TASK-IA-01: /saude e /skills; /opiniao entra na TASK-IA-02."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
import urllib.error
import urllib.request

from fastapi import FastAPI, HTTPException

from app import skills as skills_mod
from app.config import Settings
from app.contexto import ContextoRag
from app.modelos import PedidoOpiniao, PedidoOpiniaoAtivo, RespostaOpiniao, RespostaOpiniaoAtivo
from app.orquestrador import opinar, opinar_ativo
from app.provedores.cadeia import montar_cadeia

from app.chat.api import router as chat_router  # noqa: E402

app = FastAPI(title="insider-ia-b3-ecossytem", version="0.1.0")
app.include_router(chat_router)

AVISO = "Leitura automática dos números, regra experimental. Não é recomendação de investimento."


def _estado_do_indice(settings: Settings) -> dict:
    """Trechos no indice do RAG e a data do arquivo (ultima indexacao). Nunca levanta."""
    caminho = settings.rag_indice
    if not caminho.is_file():
        return {"trechos": 0, "ultima_indexacao": None}
    try:
        conexao = sqlite3.connect(f"file:{caminho.as_posix()}?mode=ro", uri=True, timeout=2)
        try:
            total = conexao.execute("SELECT COUNT(*) FROM trecho").fetchone()[0]
        finally:
            conexao.close()
    except sqlite3.Error:
        return {"trechos": 0, "ultima_indexacao": None}
    quando = datetime.fromtimestamp(caminho.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds")
    return {"trechos": int(total), "ultima_indexacao": quando}


def _estado_do_ollama(settings: Settings) -> dict:
    """Pergunta ao Ollama quais modelos tem e se o de chat esta baixado. Nunca levanta."""
    try:
        with urllib.request.urlopen(f"{settings.ollama_url}/api/tags", timeout=3) as resposta:  # noqa: S310
            nomes = [m.get("name") for m in json.loads(resposta.read()).get("models", [])]
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return {"alcancavel": False, "modelo_chat_baixado": False}
    return {"alcancavel": True, "modelo_chat_baixado": settings.modelo_chat in nomes}


@app.get("/saude")
def saude() -> dict:
    """Sempre 200 enquanto o processo vive; `status` diz se o conjunto esta pronto para opinar."""
    settings = Settings.do_ambiente()
    conjunto = skills_mod.listar(settings.dir_skills)
    ollama = _estado_do_ollama(settings)
    pronto = ollama["alcancavel"] and ollama["modelo_chat_baixado"]
    return {
        "status": "OK" if pronto else "DEGRADADO",
        "modelo": settings.modelo_chat,
        "ollama": ollama,
        "skills_versao": skills_mod.versao_do_conjunto(conjunto),
        "skills": len(conjunto),
        "indice": _estado_do_indice(settings),
        "aviso": AVISO,
    }


@app.post("/opiniao", response_model=RespostaOpiniao)
def opiniao(pedido: PedidoOpiniao) -> RespostaOpiniao:
    """CTR-IA-01: um horizonte por chamada. Nunca devolve 5xx por falha do modelo (cai na regra)."""
    settings = Settings.do_ambiente()
    conjunto = skills_mod.listar(settings.dir_skills)
    provedor = montar_cadeia(settings, "lote")
    escolhidas = skills_mod.selecionar(conjunto, pedido.horizonte_pregoes, [e.id for e in pedido.evidencias])
    return opinar(pedido, provedor, skills_mod.versao_do_conjunto(conjunto),
                  sistema=skills_mod.montar_sistema(escolhidas) or None,
                  schema=skills_mod.schema_da_resposta(settings.dir_skills),
                  contexto=ContextoRag(settings.rag_indice) if settings.rag_indice.is_file() else None)


@app.post("/opiniao/ativo", response_model=RespostaOpiniaoAtivo)
def opiniao_do_ativo(pedido: PedidoOpiniaoAtivo) -> RespostaOpiniaoAtivo:
    """CTR-IA-01 v1.1 (SPEC 13.3): os horizontes do ativo numa chamada ao modelo, validados item a item.

    200 sempre que o corpo for valido (falha do modelo vira regra no item); 422 so para corpo invalido.
    """
    settings = Settings.do_ambiente()
    conjunto = skills_mod.listar(settings.dir_skills)
    provedor = montar_cadeia(settings, "lote")
    ids = [e.id for h in pedido.horizontes for e in h.evidencias]
    escolhidas: list = []
    for h in pedido.horizontes:
        for s in skills_mod.selecionar(conjunto, h.horizonte_pregoes, ids):
            if s not in escolhidas:
                escolhidas.append(s)
    return opinar_ativo(pedido, provedor, skills_mod.versao_do_conjunto(conjunto),
                        sistema=skills_mod.montar_sistema(escolhidas) or None,
                        schema_do_item=skills_mod.schema_da_resposta(settings.dir_skills),
                        contexto=ContextoRag(settings.rag_indice) if settings.rag_indice.is_file() else None)


@app.post("/indexar")
def indexar_conhecimento() -> dict:
    """REQ-IA-06: (re)indexa as fichas alteradas (por hash do trecho). Sem Ollama, so indice textual."""
    settings = Settings.do_ambiente()
    try:
        from app.rag import embeddings  # noqa: PLC0415 - modulo da TASK-IA-10
        from app.rag.indexador import indexar  # noqa: PLC0415
    except ImportError as erro:
        raise HTTPException(status_code=501, detail=f"indexador indisponivel: {erro}") from erro
    embedder = embeddings.criar(settings.ollama_url, settings.modelo_embed)
    resumo = indexar(settings.dir_conhecimento, settings.rag_indice, embedder)
    return {"indice": str(settings.rag_indice.name), **{k: getattr(resumo, k) for k in
            ("novos", "removidos", "inalterados", "com_vetor", "total") if hasattr(resumo, k)}}


@app.get("/skills")
def listar_skills() -> dict:
    conjunto = skills_mod.listar(Settings.do_ambiente().dir_skills)
    return {
        "versao": skills_mod.versao_do_conjunto(conjunto),
        "skills": [{"nome": s.nome, "versao": s.versao, "hash": s.hash} for s in conjunto],
    }
