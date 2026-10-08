"""Contexto do chat (TASK-IA-32, SPEC GEM-4, P-4).

Monta o bloco de contexto para o sistema:
  1. Trechos do RAG relevantes à pergunta (app.rag, filtro P-4).
  2. Pacote do ativo (GETs diretos ao gestor) quando `simbolo` for informado.

Nada aqui levanta exceção para o chamador: falhas viram string vazia ou ausente.
P-4: nenhuma informação com data posterior ao pregão entra no contexto.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any

log = logging.getLogger("ia-chat")

MAX_TRECHOS_RAG = 4
MAX_BYTES_GESTOR = 4096
_AVISO = "Leitura automática dos números, regra experimental. Não é recomendação de investimento."


def _get_gestor(url: str, timeout: int = 5) -> dict | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:  # noqa: S310
            corpo = r.read(MAX_BYTES_GESTOR)
            return json.loads(corpo)
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return None


def montar_pacote_ativo(simbolo: str, gestor_url: str) -> str:
    """Solicita cotação, fundamentos, opinião e comunicados do gestor; devolve bloco formatado."""
    base = gestor_url.rstrip("/")
    cotacao = _get_gestor(f"{base}/ativos/robusto/{simbolo}")
    fundamentos = _get_gestor(f"{base}/analises/{simbolo}/fundamentos")
    opiniao = _get_gestor(f"{base}/ativos/{simbolo}/opiniao")
    comunicados = _get_gestor(f"{base}/empresas/{simbolo}/comunicados")

    partes: list[str] = [f"=== Pacote do ativo {simbolo} ==="]
    if cotacao:
        partes.append(f"Cotação: {json.dumps(cotacao, ensure_ascii=False)}")
    if fundamentos:
        partes.append(f"Fundamentos: {json.dumps(fundamentos, ensure_ascii=False)}")
    if opiniao:
        partes.append(f"Opinião: {json.dumps(opiniao, ensure_ascii=False)}")
    if comunicados:
        partes.append(f"Comunicados: {json.dumps(comunicados, ensure_ascii=False)}")
    if len(partes) == 1:
        return ""
    return "\n".join(partes)


def montar_trechos_rag(pergunta: str, rag_indice: Path, data_pregao: date | None) -> str:
    """Busca trechos relevantes no índice RAG e devolve bloco formatado."""
    if not rag_indice.is_file():
        return ""
    try:
        from app.rag import busca  # noqa: PLC0415
    except ImportError:
        return ""
    try:
        hoje = data_pregao or date.today()
        trechos = busca.buscar(
            consulta=pergunta,
            caminho_indice=rag_indice,
            disponivel_ate=hoje,
            max_resultados=MAX_TRECHOS_RAG,
        )
    except Exception:  # noqa: BLE001
        return ""
    if not trechos:
        return ""
    linhas = [f"=== Trechos do RAG (ponto no tempo: {hoje}) ==="]
    for t in trechos:
        linhas.append(f"[trecho_id={t.trecho_id}] {t.fonte}: {t.texto[:500]}")
    return "\n".join(linhas)


def montar_contexto(pergunta: str, rag_indice: Path, gestor_url: str,
                    simbolo: str | None = None, data_pregao: date | None = None) -> str:
    """Contexto completo para o sistema do chat (RAG + ativo quando houver símbolo)."""
    partes: list[str] = []

    trechos = montar_trechos_rag(pergunta, rag_indice, data_pregao)
    if trechos:
        partes.append(trechos)

    if simbolo:
        pacote = montar_pacote_ativo(simbolo, gestor_url)
        if pacote:
            partes.append(pacote)

    if partes:
        partes.append(f"\n{_AVISO}")
    return "\n\n".join(partes)
