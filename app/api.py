"""API do servico de IA (SPEC 5). TASK-IA-01: /saude e /skills; /opiniao entra na TASK-IA-02."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from fastapi import FastAPI

from app import skills as skills_mod
from app.config import Settings
from app.modelos import PedidoOpiniao, RespostaOpiniao
from app.orquestrador import opinar
from app.provedores.ollama import OllamaProvedor

app = FastAPI(title="insider-ia-b3-ecossytem", version="0.1.0")

AVISO = "Leitura automática dos números, regra experimental. Não é recomendação de investimento."


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
        "indice": {"trechos": 0, "ultima_indexacao": None},
        "aviso": AVISO,
    }


@app.post("/opiniao", response_model=RespostaOpiniao)
def opiniao(pedido: PedidoOpiniao) -> RespostaOpiniao:
    """CTR-IA-01: um horizonte por chamada. Nunca devolve 5xx por falha do modelo (cai na regra)."""
    settings = Settings.do_ambiente()
    conjunto = skills_mod.listar(settings.dir_skills)
    provedor = OllamaProvedor(settings.ollama_url, settings.modelo_chat, timeout_s=settings.timeout_modelo_s)
    return opinar(pedido, provedor, skills_mod.versao_do_conjunto(conjunto))


@app.get("/skills")
def listar_skills() -> dict:
    conjunto = skills_mod.listar(Settings.do_ambiente().dir_skills)
    return {
        "versao": skills_mod.versao_do_conjunto(conjunto),
        "skills": [{"nome": s.nome, "versao": s.versao, "hash": s.hash} for s in conjunto],
    }
