"""TASK-IA-27 (configuracao): variaveis do Gemini, limites por modelo e validacao."""

from __future__ import annotations

import pytest

from app.config import ConfiguracaoInvalida, LimiteDeModelo, Settings

VARIAVEIS = (
    "GEMINI_API_KEY", "GEMINI_MODELOS", "GEMINI_LIMITES", "GEMINI_RPM", "GEMINI_RPD", "GEMINI_TIMEOUT_S",
    "PROVEDORES_LOTE", "PROVEDORES_CHAT", "COTA_CHAT_PCT", "COTA_CARD_PCT", "COTA_LOTE_PCT",
    "CHAT_MAX_DIA_SESSAO", "CHAT_INTERVALO_S",
)


@pytest.fixture(autouse=True)
def ambiente_limpo(monkeypatch):
    for nome in VARIAVEIS:
        monkeypatch.delenv(nome, raising=False)


def test_padroes_seguem_a_dec_ia_10():
    cfg = Settings.do_ambiente()
    assert cfg.gemini_modelos == ("gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.8-flash")
    assert cfg.gemini_limites == (LimiteDeModelo(15, 500), LimiteDeModelo(15, 500), LimiteDeModelo(5, 20))
    assert cfg.provedores_lote == ("gemini",)
    assert cfg.provedores_chat == ("gemini",)
    assert (cfg.cota_chat_pct, cfg.cota_card_pct, cfg.cota_lote_pct) == (40, 20, 40)
    assert (cfg.chat_max_dia_sessao, cfg.chat_intervalo_s, cfg.gemini_timeout_s) == (60, 3, 30)


def test_sem_chave_o_gemini_fica_indisponivel_mas_o_servico_configura():
    cfg = Settings.do_ambiente()
    assert cfg.gemini_api_key == ""
    assert cfg.gemini_configurado is False


def test_com_chave_o_gemini_fica_configurado(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "  chave-de-teste  ")
    cfg = Settings.do_ambiente()
    assert cfg.gemini_api_key == "chave-de-teste"
    assert cfg.gemini_configurado is True


def test_limites_com_menos_itens_completam_com_a_reserva(monkeypatch):
    monkeypatch.setenv("GEMINI_LIMITES", "15/500")
    monkeypatch.setenv("GEMINI_RPM", "7")
    monkeypatch.setenv("GEMINI_RPD", "30")
    cfg = Settings.do_ambiente()
    assert cfg.gemini_limites == (LimiteDeModelo(15, 500), LimiteDeModelo(7, 30), LimiteDeModelo(7, 30))


def test_modelos_e_limites_customizados(monkeypatch):
    monkeypatch.setenv("GEMINI_MODELOS", " m1 , m2 ")
    monkeypatch.setenv("GEMINI_LIMITES", "10/100,2/5")
    cfg = Settings.do_ambiente()
    assert cfg.gemini_modelos == ("m1", "m2")
    assert cfg.gemini_limites == (LimiteDeModelo(10, 100), LimiteDeModelo(2, 5))


def test_sem_modelos_o_gemini_nao_fica_configurado_mesmo_com_chave(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "x")
    monkeypatch.setenv("GEMINI_MODELOS", "")
    monkeypatch.setenv("GEMINI_LIMITES", "")
    assert Settings.do_ambiente().gemini_configurado is False


@pytest.mark.parametrize("limites", ["15/500/9x", "abc", "15", "0/10", "10/0", "a/b", "15/500,15/500,5/20,1/1"])
def test_limites_invalidos_sao_recusados(monkeypatch, limites):
    monkeypatch.setenv("GEMINI_LIMITES", limites)
    with pytest.raises(ConfiguracaoInvalida):
        Settings.do_ambiente()


def test_provedor_desconhecido_e_recusado(monkeypatch):
    monkeypatch.setenv("PROVEDORES_CHAT", "gemini,openai")
    with pytest.raises(ConfiguracaoInvalida, match="openai"):
        Settings.do_ambiente()


def test_cotas_precisam_somar_100(monkeypatch):
    monkeypatch.setenv("COTA_CHAT_PCT", "50")
    with pytest.raises(ConfiguracaoInvalida, match="100"):
        Settings.do_ambiente()


def test_numero_invalido_diz_qual_variavel(monkeypatch):
    monkeypatch.setenv("GEMINI_TIMEOUT_S", "rapido")
    with pytest.raises(ConfiguracaoInvalida, match="GEMINI_TIMEOUT_S"):
        Settings.do_ambiente()
