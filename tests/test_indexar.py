"""REQ-IA-06: POST /indexar usa o indexador da IA-10 e responde o resumo; sem o modulo, 501."""

from __future__ import annotations

import sys
import types

from fastapi.testclient import TestClient

from app.api import app


def _falso_rag(monkeypatch, resumo):
    pacote = types.ModuleType("app.rag")
    idx = types.ModuleType("app.rag.indexador")
    idx.indexar = lambda dir_conhecimento, caminho, embedder=None: resumo
    pacote.indexador = idx
    monkeypatch.setitem(sys.modules, "app.rag", pacote)
    monkeypatch.setitem(sys.modules, "app.rag.indexador", idx)


class _Resumo:
    novos, removidos, inalterados, com_vetor, total = 3, 1, 10, False, 14


def test_indexar_devolve_o_resumo(monkeypatch, tmp_path):
    monkeypatch.setenv("RAG_INDICE", str(tmp_path / "rag.sqlite"))
    _falso_rag(monkeypatch, _Resumo())
    corpo = TestClient(app).post("/indexar").json()
    assert corpo == {"indice": "rag.sqlite", "novos": 3, "removidos": 1, "inalterados": 10,
                     "com_vetor": False, "total": 14}


def test_indexar_sem_modulo_responde_501(monkeypatch):
    for nome in ("app.rag", "app.rag.indexador"):
        monkeypatch.setitem(sys.modules, nome, None)  # forca ImportError
    assert TestClient(app).post("/indexar").status_code == 501
