"""TASK-IA-32: testes do módulo de contexto do chat."""

from __future__ import annotations

import json
import threading
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from app.chat.contexto import montar_contexto, montar_pacote_ativo, montar_trechos_rag


# ---------------------------------------------------------------------------
# montar_pacote_ativo — com servidor HTTP falso
# ---------------------------------------------------------------------------

class GestorFalso(BaseHTTPRequestHandler):
    def log_message(self, *args): pass

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if "robusto" in self.path:
            self.wfile.write(json.dumps({"fechamento": 52.1, "variacao_1d": 0.012}).encode())
        elif "fundamentos" in self.path:
            self.wfile.write(json.dumps({"pl": 18.4, "roe": 0.21}).encode())
        elif "opiniao" in self.path:
            self.wfile.write(json.dumps({"horizonte_pregoes": 5, "opiniao": "neutro"}).encode())
        elif "comunicados" in self.path:
            self.wfile.write(json.dumps([{"titulo": "Ata", "data": "2026-10-01"}]).encode())
        else:
            self.wfile.write(b"{}")


@pytest.fixture(scope="module")
def gestor_url():
    servidor = HTTPServer(("127.0.0.1", 0), GestorFalso)
    port = servidor.server_address[1]
    t = threading.Thread(target=servidor.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{port}"
    servidor.shutdown()


def test_montar_pacote_ativo_inclui_campos(gestor_url):
    texto = montar_pacote_ativo("PETR4", gestor_url)
    assert "PETR4" in texto
    assert "52.1" in texto or "52,1" in texto or "fechamento" in texto


def test_montar_pacote_ativo_gestor_fora():
    texto = montar_pacote_ativo("PETR4", "http://127.0.0.1:9")  # porta fechada
    assert texto == ""


# ---------------------------------------------------------------------------
# montar_trechos_rag — sem índice real
# ---------------------------------------------------------------------------

def test_montar_trechos_rag_sem_indice(tmp_path):
    texto = montar_trechos_rag("PETR4 cotação", tmp_path / "inexistente.sqlite", date.today())
    assert texto == ""


# ---------------------------------------------------------------------------
# montar_contexto — integração
# ---------------------------------------------------------------------------

def test_montar_contexto_com_simbolo_retorna_pacote(gestor_url, tmp_path):
    ctx = montar_contexto(
        pergunta="qual a cotação de PETR4?",
        rag_indice=tmp_path / "vazio.sqlite",
        gestor_url=gestor_url,
        simbolo="PETR4",
    )
    assert "PETR4" in ctx


def test_montar_contexto_sem_simbolo_retorna_vazio(gestor_url, tmp_path):
    ctx = montar_contexto(
        pergunta="o que é P/L?",
        rag_indice=tmp_path / "vazio.sqlite",
        gestor_url=gestor_url,
        simbolo=None,
    )
    # Sem RAG e sem símbolo: vazio
    assert ctx == ""


def test_montar_contexto_contem_aviso_cvm(gestor_url, tmp_path):
    ctx = montar_contexto(
        pergunta="PETR4",
        rag_indice=tmp_path / "vazio.sqlite",
        gestor_url=gestor_url,
        simbolo="PETR4",
    )
    assert "recomendação" in ctx.lower() or "experimental" in ctx.lower()
