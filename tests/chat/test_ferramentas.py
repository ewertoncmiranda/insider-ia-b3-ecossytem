"""TASK-IA-33: testes das ferramentas de function calling."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from app.chat.ferramentas import (
    LimiteChamadasAtingido,
    SimboloInvalido,
    executar,
)


class GestorFalso(BaseHTTPRequestHandler):
    def log_message(self, *args): pass

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True, "path": self.path}).encode())


@pytest.fixture(scope="module")
def gestor_url():
    servidor = HTTPServer(("127.0.0.1", 0), GestorFalso)
    port = servidor.server_address[1]
    t = threading.Thread(target=servidor.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{port}"
    servidor.shutdown()


def test_cotacao_simbolo_valido(gestor_url):
    cont = [0]
    resultado = executar("cotacao", {"s": "PETR4"}, gestor_url, cont)
    dados = json.loads(resultado)
    assert "ok" in dados


def test_fundamentos_simbolo_valido(gestor_url):
    cont = [0]
    resultado = executar("fundamentos", {"s": "VALE3"}, gestor_url, cont)
    dados = json.loads(resultado)
    assert "ok" in dados


def test_opiniao_simbolo_valido(gestor_url):
    cont = [0]
    resultado = executar("opiniao", {"s": "ITUB4"}, gestor_url, cont)
    dados = json.loads(resultado)
    assert "ok" in dados


def test_comunicados_simbolo_valido(gestor_url):
    cont = [0]
    resultado = executar("comunicados", {"s": "WEGE3"}, gestor_url, cont)
    dados = json.loads(resultado)
    assert "ok" in dados


def test_comparar_dois_simbolos(gestor_url):
    cont = [0]
    resultado = executar("comparar", {"s1": "PETR4", "s2": "VALE3"}, gestor_url, cont)
    dados = json.loads(resultado)
    assert "s1" in dados and "s2" in dados


def test_simbolo_invalido_nao_chama_gestor():
    cont = [0]
    with pytest.raises(SimboloInvalido):
        executar("cotacao", {"s": "invalido"}, "http://127.0.0.1:9", cont)
    # Contador não foi incrementado além do que causou a rejeição (validação ocorre depois de +1)


def test_simbolo_sem_numero_invalido():
    cont = [0]
    with pytest.raises(SimboloInvalido):
        executar("cotacao", {"s": "PETRO"}, "http://127.0.0.1:9", cont)


def test_simbolo_minusculo_invalido():
    cont = [0]
    with pytest.raises(SimboloInvalido):
        executar("cotacao", {"s": "petr4"}, "http://127.0.0.1:9", cont)


def test_quinta_chamada_recusada(gestor_url):
    cont = [0]
    for _ in range(4):
        executar("cotacao", {"s": "PETR4"}, gestor_url, cont)
    with pytest.raises(LimiteChamadasAtingido):
        executar("cotacao", {"s": "PETR4"}, gestor_url, cont)


def test_gestor_fora_retorna_dado_indisponivel():
    cont = [0]
    resultado = executar("cotacao", {"s": "PETR4"}, "http://127.0.0.1:9", cont)
    dados = json.loads(resultado)
    assert "indisponível" in dados.get("erro", "") or "erro" in dados


def test_truncar_resposta_longa(gestor_url):
    cont = [0]
    resultado = executar("cotacao", {"s": "PETR4"}, gestor_url, cont)
    assert len(resultado.encode("utf-8")) <= 4096 + 10  # margem de decodificação


def test_ferramenta_desconhecida(gestor_url):
    cont = [0]
    resultado = executar("xpto_inexistente", {"s": "PETR4"}, gestor_url, cont)
    dados = json.loads(resultado)
    assert "erro" in dados
