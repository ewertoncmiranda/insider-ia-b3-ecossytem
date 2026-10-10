"""TASK-IA-25: governador de cota com relogio falso.

Outubro de 2026: Los Angeles em PDT (UTC-7, zera as 07:00 UTC) e Sao Paulo em UTC-3 (18h = 21:00 UTC).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.cota import GovernadorCota, chave_cache, dia_cota, proximo_zeramento

PADRAO = {"gemini-3.5-flash-lite": (15, 500), "gemini-3.1-flash-lite": (15, 500), "gemini-3.8-flash": (5, 20)}


class Relogio:
    def __init__(self, inicio: datetime):
        self.t = inicio

    def __call__(self) -> datetime:
        return self.t

    def andar(self, **kw) -> None:
        self.t += timedelta(**kw)


def utc(dia: int, hora: int, minuto: int = 0) -> datetime:
    return datetime(2026, 10, dia, hora, minuto, tzinfo=timezone.utc)


@pytest.fixture
def relogio():
    return Relogio(utc(8, 13))  # 10h em Sao Paulo, 06h em Los Angeles


def governador(tmp_path, relogio, limites=None, **kw):
    return GovernadorCota(tmp_path / "cota.sqlite", PADRAO if limites is None else limites, agora=relogio, **kw)


def test_limites_por_modelo_rpm(tmp_path, relogio):
    gov = governador(tmp_path, relogio)
    assert all(gov.reservar("chat", "gemini-3.5-flash-lite").permitido for _ in range(15))
    negado = gov.reservar("chat", "gemini-3.5-flash-lite")
    assert (negado.permitido, negado.motivo) == (False, "rpm")
    assert negado.tentar_apos == relogio.t + timedelta(seconds=60)

    assert all(gov.reservar("chat", "gemini-3.8-flash").permitido for _ in range(5))
    assert gov.reservar("chat", "gemini-3.8-flash").motivo == "rpm"
    # o outro modelo tem a sua propria conta
    assert gov.reservar("chat", "gemini-3.1-flash-lite").permitido

    relogio.andar(seconds=61)
    assert gov.reservar("chat", "gemini-3.8-flash").permitido


def test_limites_por_modelo_rpd_e_zeramento_em_los_angeles(tmp_path, relogio):
    gov = governador(tmp_path, relogio)
    for _ in range(4):  # 20 chamadas do Flash em 4 minutos
        assert all(gov.reservar("chat", "gemini-3.8-flash").permitido for _ in range(5))
        relogio.andar(seconds=61)
    negado = gov.reservar("chat", "gemini-3.8-flash")
    assert negado.motivo == "rpd"
    assert negado.tentar_apos == utc(9, 7)  # meia-noite de Los Angeles
    assert gov.reservar("chat", "gemini-3.5-flash-lite").permitido  # Flash Lite tem 500

    relogio.t = utc(9, 6, 59)
    assert gov.reservar("chat", "gemini-3.8-flash").motivo == "rpd"
    relogio.t = utc(9, 7)
    assert gov.reservar("chat", "gemini-3.8-flash").permitido
    assert gov.estado_modelos()[2] == {"nome": "gemini-3.8-flash", "em_pausa_ate": None, "usadas_hoje": 1, "teto_dia": 20}


def test_dia_da_cota_segue_o_horario_de_verao_de_los_angeles():
    assert dia_cota(utc(8, 6, 59)) == "2026-10-07"
    assert dia_cota(utc(8, 7)) == "2026-10-08"
    # 1/11/2026 acaba o horario de verao: em novembro o zeramento passa para 08:00 UTC
    assert proximo_zeramento(datetime(2026, 11, 10, 12, tzinfo=timezone.utc)) == datetime(2026, 11, 11, 8, tzinfo=timezone.utc)


def test_pausa_de_429(tmp_path, relogio):
    gov = governador(tmp_path, relogio)
    m = "gemini-3.5-flash-lite"
    gov.pausar(m, espera_s=17)
    negado = gov.reservar("chat", m)
    assert (negado.motivo, negado.tentar_apos) == ("pausa", relogio.t + timedelta(seconds=17))
    assert gov.estado_modelos()[0]["em_pausa_ate"] == (relogio.t + timedelta(seconds=17)).isoformat()
    relogio.andar(seconds=18)
    assert gov.reservar("chat", m).permitido

    assert gov.pausar(m) == relogio.t + timedelta(seconds=60)  # sem retryDelay: 60 s
    assert gov.pausar(m, espera_s=1) == relogio.t + timedelta(seconds=60)  # nao encurta
    assert gov.pausar(m, diaria=True) == utc(9, 7)  # cota diaria: ate o zeramento
    relogio.t = utc(9, 7)
    assert gov.reservar("chat", m).permitido


def test_teto_por_balde_antes_das_18h(tmp_path, relogio):
    gov = governador(tmp_path, relogio, limites={"m": (1000, 10)})  # teto 10: chat 4, card 2, lote 4
    assert (gov.teto_balde("chat"), gov.teto_balde("card"), gov.teto_balde("lote")) == (4, 2, 4)
    assert gov.reservar("card", "m").permitido and gov.reservar("card", "m").permitido
    negado = gov.reservar("card", "m")
    assert negado.motivo == "balde"
    assert negado.tentar_apos == utc(8, 21)  # 18h de Sao Paulo, quando a sobra libera
    assert gov.restante("card") == 0
    assert gov.reservar("chat", "m").permitido  # outro balde segue


def test_sobra_apos_18h(tmp_path, relogio):
    gov = governador(tmp_path, relogio, limites={"m": (1000, 10)})
    gov.reservar("card", "m")
    gov.reservar("card", "m")
    relogio.t = utc(8, 21, 30)  # 18h30 em Sao Paulo
    assert gov.restante("card") == 8
    assert all(gov.reservar("card", "m").permitido for _ in range(8))
    negado = gov.reservar("card", "m")  # teto do dia acabou (com um modelo, e o RPD dele)
    assert (negado.permitido, negado.tentar_apos) == (False, utc(9, 7))


def test_corte_do_lote_abaixo_de_15_por_cento(tmp_path, relogio):
    gov = governador(tmp_path, relogio, limites={"m": (1000, 100)})  # limiar = 15 chamadas
    relogio.t = utc(8, 22)  # depois das 18h: o chat pode gastar a sobra
    for _ in range(85):
        assert gov.reservar("chat", "m").permitido
    assert gov.restante("lote") == 1
    assert gov.reservar("lote", "m").permitido  # restavam 15 (= 15%): ainda passa
    negado = gov.reservar("lote", "m")  # restam 14 (< 15%)
    assert negado.motivo == "corte_lote"
    assert gov.restante("lote") == 0
    assert gov.gemini_disponivel("lote") is False
    assert gov.reservar("chat", "m").permitido and gov.reservar("card", "m").permitido  # prioridade


def test_cache_impede_segunda_cobranca(tmp_path, relogio):
    gov = governador(tmp_path, relogio)
    chamadas = []

    def chamar(prompt: str) -> str:
        chave = chave_cache("gemini", "gemini-3.5-flash-lite", prompt, {"type": "object"})
        if (guardado := gov.cache_obter(chave)) is not None:
            return guardado
        assert gov.reservar("card", "gemini-3.5-flash-lite").permitido
        chamadas.append(prompt)
        gov.cache_gravar(chave, "resposta")
        return "resposta"

    assert chamar("Leia  WEGE3\nhoje") == "resposta"
    assert chamar("Leia WEGE3 hoje") == "resposta"  # mesmo prompt normalizado
    assert len(chamadas) == 1
    assert gov.estado_modelos()[0]["usadas_hoje"] == 1
    relogio.t = utc(9, 7)  # outro dia de cota: cache vencido
    chamar("Leia WEGE3 hoje")
    assert len(chamadas) == 2


def test_chave_de_cache_estavel():
    a = chave_cache("gemini", "m", "x  y", {"b": 1, "a": 2})
    assert a == chave_cache("gemini", "m", "x y", {"a": 2, "b": 1})
    assert a != chave_cache("gemini", "outro", "x y", {"a": 2, "b": 1})
    assert a != chave_cache("outro-provedor", "m", "x y", {"a": 2, "b": 1})


def test_conta_persiste_entre_instancias(tmp_path, relogio):
    governador(tmp_path, relogio).reservar("lote", "gemini-3.8-flash")
    assert governador(tmp_path, relogio).estado_modelos()[2]["usadas_hoje"] == 1


def test_teto_padrao_e_reserva_para_modelo_sem_limite(tmp_path, relogio):
    gov = governador(tmp_path, relogio)
    assert gov.teto_dia == 1020
    assert (gov.teto_balde("chat"), gov.teto_balde("card"), gov.teto_balde("lote")) == (408, 204, 408)
    assert gov.limite("modelo-novo") == (5, 20)
    assert all(gov.reservar("chat", "modelo-novo").permitido for _ in range(5))
    assert gov.reservar("chat", "modelo-novo").motivo == "rpm"


def test_entradas_invalidas(tmp_path, relogio):
    with pytest.raises(ValueError):
        governador(tmp_path, relogio, pct={"chat": 50, "card": 20, "lote": 40})
    with pytest.raises(ValueError):
        governador(tmp_path, relogio).reservar("outro", "m")
    with pytest.raises(ValueError):
        governador(tmp_path, relogio, limites={"m": (0, 10)})
