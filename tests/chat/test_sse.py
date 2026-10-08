"""TASK-IA-30: testes do endpoint POST /chat e do módulo sse.py."""

from __future__ import annotations

import json

import pytest

from app.chat import sse


# ---------------------------------------------------------------------------
# sse.py — formatação dos eventos
# ---------------------------------------------------------------------------

def test_formato_basico():
    evt = sse.evento("token", {"texto": "olá"})
    assert evt.startswith("event: token\ndata: ")
    assert evt.endswith("\n\n")
    dados = json.loads(evt.split("data: ", 1)[1].strip())
    assert dados == {"texto": "olá"}


def test_inicio():
    evt = sse.inicio("gemini-flash", "sess-1")
    dados = json.loads(evt.split("data: ", 1)[1].strip())
    assert dados["modelo"] == "gemini-flash"
    assert dados["sessao_id"] == "sess-1"


def test_token():
    evt = sse.token("pedaço de texto")
    dados = json.loads(evt.split("data: ", 1)[1].strip())
    assert dados["texto"] == "pedaço de texto"


def test_fontes():
    lista = [{"tipo": "ficha", "rotulo": "PETR4 Q1", "ref": "trecho_001"}]
    evt = sse.fontes(lista)
    dados = json.loads(evt.split("data: ", 1)[1].strip())
    assert dados["fontes"] == lista


def test_aviso():
    evt = sse.aviso("número sem fonte: 12,4%")
    dados = json.loads(evt.split("data: ", 1)[1].strip())
    assert dados["texto"] == "número sem fonte: 12,4%"


def test_fim():
    evt = sse.fim(123, 41)
    dados = json.loads(evt.split("data: ", 1)[1].strip())
    assert dados["tokens_saida"] == 123
    assert dados["restante_hoje"] == 41


def test_erro():
    evt = sse.erro("INDISPONIVEL", "fora do ar", "2026-10-08T15:00:00Z")
    dados = json.loads(evt.split("data: ", 1)[1].strip())
    assert dados["codigo"] == "INDISPONIVEL"
    assert dados["tentar_apos"] == "2026-10-08T15:00:00Z"


def test_erro_sem_tentar_apos():
    evt = sse.erro("FORA_DO_TEMA", "fora do escopo")
    dados = json.loads(evt.split("data: ", 1)[1].strip())
    assert dados["tentar_apos"] is None


# ---------------------------------------------------------------------------
# POST /chat — endpoint (usando TestClient)
# ---------------------------------------------------------------------------

def _parse_eventos(body: bytes) -> list[dict]:
    eventos = []
    bloco_tipo = None
    for linha in body.decode("utf-8").splitlines():
        if linha.startswith("event: "):
            bloco_tipo = linha[7:].strip()
        elif linha.startswith("data: ") and bloco_tipo:
            dados = json.loads(linha[6:])
            eventos.append({"tipo": bloco_tipo, "dados": dados})
            bloco_tipo = None
    return eventos


def _cliente():
    from fastapi.testclient import TestClient
    from app.api import app
    return TestClient(app)


def test_sem_gemini_retorna_indisponivel(monkeypatch):
    """Sem Gemini configurado → único evento 'erro' com código INDISPONIVEL."""
    import app.chat.api as api_mod
    monkeypatch.setattr(api_mod, "_gemini_provedores", lambda s: [])

    c = _cliente()
    r = c.post("/chat", json={"sessao_id": "s1", "mensagem": "o que é PETR4?"})
    assert r.status_code == 200
    evts = _parse_eventos(r.content)
    assert len(evts) == 1
    assert evts[0]["tipo"] == "erro"
    assert evts[0]["dados"]["codigo"] == "INDISPONIVEL"


def test_fora_do_tema_retorna_erro():
    """Mensagem fora de mercado financeiro → 'erro' com código FORA_DO_TEMA."""
    c = _cliente()
    r = c.post("/chat", json={"sessao_id": "s2", "mensagem": "receita de bolo de chocolate com 3 xícaras de farinha"})
    assert r.status_code == 200
    evts = _parse_eventos(r.content)
    assert any(e["tipo"] == "erro" and e["dados"]["codigo"] == "FORA_DO_TEMA" for e in evts)


def test_ordem_eventos_com_gemini_fake(monkeypatch, tmp_path):
    """Com provedor falso: inicio → token* → fim (sem erro)."""
    import app.chat.api as api_mod
    from types import SimpleNamespace

    class FakeProvedor:
        nome = "gemini-3.5-flash-lite"

        def conversar(self, mensagens, sistema):
            yield "resposta "
            yield "de teste"

    monkeypatch.setattr(api_mod, "_gemini_provedores", lambda s: [FakeProvedor()])
    monkeypatch.setattr(api_mod, "_contexto", lambda p, s, sim: "")

    # Sessão sem histórico
    class FakeSessoes:
        def total_hoje(self, sid): return 0
        def ultima_mensagem_usuario(self, sid): return None
        def carregar(self, sid): return []
        def adicionar(self, sid, papel, texto): pass
        def fechar(self): pass

    monkeypatch.setattr(api_mod, "_sessoes", lambda s: FakeSessoes())

    c = _cliente()
    r = c.post("/chat", json={"sessao_id": "s3", "mensagem": "o que é PETR4?"})
    assert r.status_code == 200
    evts = _parse_eventos(r.content)

    tipos = [e["tipo"] for e in evts]
    assert tipos[0] == "inicio"
    assert "token" in tipos
    assert tipos[-1] == "fim"
    # Nenhum erro
    assert "erro" not in tipos


def test_simbolo_invalido_retorna_422():
    c = _cliente()
    r = c.post("/chat", json={"sessao_id": "s4", "mensagem": "ok", "simbolo": "INVALIDO"})
    assert r.status_code == 422
