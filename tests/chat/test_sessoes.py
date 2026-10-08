"""TASK-IA-31: testes de sessões do chat (SQLite, expiração, resumo)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.chat.sessoes import SessoesChat, JANELA_MENSAGENS, EXPIRACAO_H, TAMANHO_RESUMO


def _ts(delta_h: float = 0) -> float:
    return datetime.now(timezone.utc).timestamp() + delta_h * 3600


def _relogio(ts: float):
    from datetime import datetime, timezone
    return lambda: datetime.fromtimestamp(ts, tz=timezone.utc)


def test_adicionar_e_carregar(tmp_path):
    s = SessoesChat(tmp_path / "sessoes.sqlite")
    s.adicionar("abc", "usuario", "oi")
    s.adicionar("abc", "modelo", "olá!")
    msgs = s.carregar("abc")
    assert len(msgs) == 2
    assert msgs[0] == {"papel": "usuario", "texto": "oi"}
    assert msgs[1] == {"papel": "modelo", "texto": "olá!"}
    s.fechar()


def test_janela_limita_a_12(tmp_path):
    s = SessoesChat(tmp_path / "s.sqlite")
    for i in range(20):
        s.adicionar("xyz", "usuario", f"msg {i}")
    msgs = s.carregar("xyz")
    assert len(msgs) == JANELA_MENSAGENS
    # Deve conter as últimas mensagens
    assert msgs[-1]["texto"] == "msg 19"
    s.fechar()


def test_total_hoje_conta_mensagens_usuario(tmp_path):
    s = SessoesChat(tmp_path / "s.sqlite")
    s.adicionar("u1", "usuario", "mensagem 1")
    s.adicionar("u1", "modelo", "resposta")
    s.adicionar("u1", "usuario", "mensagem 2")
    assert s.total_hoje("u1") == 2
    s.fechar()


def test_sessao_expirada(tmp_path):
    ts_antigo = _ts(-25)
    s = SessoesChat(tmp_path / "s.sqlite", agora=_relogio(ts_antigo))
    s.adicionar("old", "usuario", "mensagem antiga")
    s.fechar()

    s2 = SessoesChat(tmp_path / "s.sqlite", agora=_relogio(_ts()))
    assert s2.expirado("old")
    s2.fechar()


def test_sessao_nao_expirada(tmp_path):
    s = SessoesChat(tmp_path / "s.sqlite")
    s.adicionar("new", "usuario", "mensagem recente")
    assert not s.expirado("new")
    s.fechar()


def test_ultima_mensagem_usuario(tmp_path):
    s = SessoesChat(tmp_path / "s.sqlite")
    s.adicionar("u", "usuario", "msg")
    ultima = s.ultima_mensagem_usuario("u")
    assert ultima is not None
    assert abs(ultima - _ts()) < 2  # dentro de 2 segundos
    s.fechar()


def test_precisa_resumir_falso_antes_de_8(tmp_path):
    s = SessoesChat(tmp_path / "s.sqlite")
    for i in range(7):
        s.adicionar("r", "usuario", f"m{i}")
    assert not s.precisa_resumir("r")
    s.fechar()


def test_precisa_resumir_verdadeiro_apos_8(tmp_path):
    s = SessoesChat(tmp_path / "s.sqlite")
    for i in range(TAMANHO_RESUMO):
        s.adicionar("r", "usuario", f"m{i}")
    assert s.precisa_resumir("r")
    s.fechar()


def test_resumir_chama_provedor_e_comprime(tmp_path):
    class FakeProvedor:
        def gerar(self, sistema, usuario, schema):
            return "RESUMO: histórico comprimido"

    s = SessoesChat(tmp_path / "s.sqlite")
    # Adicionar 12 mensagens para ter mensagens a resumir
    for i in range(12):
        papel = "usuario" if i % 2 == 0 else "modelo"
        s.adicionar("r", papel, f"mensagem {i}")
    total_antes = s.total_acumulado("r")

    s.resumir("r", FakeProvedor())

    total_depois = s.total_acumulado("r")
    assert total_depois < total_antes
    # O resumo deve estar no histórico
    msgs = s.carregar("r")
    textos = [m["texto"] for m in msgs]
    assert any("RESUMO" in t for t in textos)
    s.fechar()


def test_resumir_com_provedor_falho_nao_levanta(tmp_path):
    class FalhaProvedor:
        def gerar(self, *args, **kwargs):
            raise RuntimeError("falha de rede")

    s = SessoesChat(tmp_path / "s.sqlite")
    for i in range(8):
        s.adicionar("r", "usuario", f"m{i}")
    # Não deve lançar exceção
    s.resumir("r", FalhaProvedor())
    s.fechar()
