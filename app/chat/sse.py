"""Formatação de eventos SSE para POST /chat (CTR-IA-02, TASK-IA-30).

Formato: event: <tipo>\\ndata: <json>\\n\\n
Cada função devolve a string já pronta para ser colocada no StreamingResponse.
"""

from __future__ import annotations

import json


def evento(tipo: str, dados: dict) -> str:
    return f"event: {tipo}\ndata: {json.dumps(dados, ensure_ascii=False)}\n\n"


def inicio(modelo: str, sessao_id: str) -> str:
    return evento("inicio", {"modelo": modelo, "sessao_id": sessao_id})


def token(texto: str) -> str:
    return evento("token", {"texto": texto})


def fontes(lista: list[dict]) -> str:
    return evento("fontes", {"fontes": lista})


def aviso(texto: str) -> str:
    return evento("aviso", {"texto": texto})


def fim(tokens_saida: int, restante_hoje: int | None = None) -> str:
    return evento("fim", {"tokens_saida": tokens_saida, "restante_hoje": restante_hoje})


def erro(codigo: str, mensagem: str, tentar_apos: str | None = None) -> str:
    return evento("erro", {"codigo": codigo, "mensagem": mensagem, "tentar_apos": tentar_apos})
