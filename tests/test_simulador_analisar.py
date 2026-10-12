"""SIM-IA-1: POST /simulador/analisar com provedor falso."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.cota import GovernadorCota
from app.simulador import analisar as mod
from app.provedores.cadeia import GEMINI, Cadeia, Elo
from app.provedores.base import ErroDoProvedor

RESULTADOS = [
    {"versao": "VALOR",          "quintil": 1, "retorno_pct": 0.041},
    {"versao": "VALOR_QUALIDADE","quintil": 1, "retorno_pct": 0.063},
    {"versao": "VALOR_MOMENTO",  "quintil": 1, "retorno_pct": 0.055},
    {"versao": "GRAHAM_V1",      "quintil": None, "retorno_pct": None},
    {"versao": "VALUATION_SETOR","quintil": 2, "retorno_pct": 0.028},
    {"versao": "MOMENTO_PURO",   "quintil": 1, "retorno_pct": 0.071},
    {"versao": "BAIXO_SPREAD",   "quintil": 1, "retorno_pct": 0.038},
]

BOA = {"analise": "WEGE3: cinco de sete estrategias em Q1. Sinal favoravel por valor e momentum. Risco: valuation acima da margem de Graham. Posicionamento: comprar."}


class Falso:
    def __init__(self, nome: str, *respostas):
        self.nome = nome
        self.respostas = list(respostas)
        self.chamadas = 0

    def gerar(self, sistema, usuario, schema):
        self.chamadas += 1
        r = self.respostas.pop(0)
        if isinstance(r, Exception):
            raise r
        return r if isinstance(r, str) else json.dumps(r)


def _cadeia(tmp_path, *provedores):
    gov = GovernadorCota(tmp_path / "cota.sqlite", {p.nome: (15, 500) for p in provedores})
    return Cadeia([Elo(GEMINI, p) for p in provedores], gov), gov


def test_analise_do_modelo_e_segunda_chamada_do_dia_nao_gasta_cota(tmp_path):
    p = Falso("g1", BOA)
    c, _ = _cadeia(tmp_path, p)
    r1 = mod.analisar("WEGE3", RESULTADOS, c)
    assert r1["origem"] == "MODELO"
    assert r1["modelo"] == "g1"
    assert r1["em_cache"] is False
    assert "WEGE3" in r1["analise"]

    resultados_embaralhados = list(reversed(RESULTADOS))
    r2 = mod.analisar("WEGE3", resultados_embaralhados, c)
    assert r2["em_cache"] is True
    assert r2["analise"] == r1["analise"]
    assert p.chamadas == 1


def test_falha_no_provedor_cai_na_regra(tmp_path):
    p = Falso("g1", ErroDoProvedor("timeout"))
    c, _ = _cadeia(tmp_path, p)
    r = mod.analisar("ITUB4", RESULTADOS, c)
    assert r["origem"] == "REGRA"
    assert r["modelo"] == "regra"
    assert r["em_cache"] is False
    assert "ITUB4" in r["analise"]
    assert r["tokens_usados"] == 0


def test_resposta_invalida_cai_na_regra(tmp_path):
    p = Falso("g1", {"analise": ""})
    c, _ = _cadeia(tmp_path, p)
    r = mod.analisar("PETR4", RESULTADOS, c)
    assert r["origem"] == "REGRA"


def test_sem_provedor_cai_na_regra():
    r = mod.analisar("VALE3", RESULTADOS, None)
    assert r["origem"] == "REGRA"
    assert "VALE3" in r["analise"]


def test_regra_sinaliza_desfavoravel_com_maioria_q5():
    ruins = [
        {"versao": f"E{i}", "quintil": 5, "retorno_pct": -0.02}
        for i in range(1, 6)
    ] + [
        {"versao": "E6", "quintil": 2, "retorno_pct": 0.01},
        {"versao": "E7", "quintil": 1, "retorno_pct": 0.02},
    ]
    r = mod.analisar("XPTO3", ruins, None)
    assert "desfavoravel" in r["analise"].lower() or "Q4-Q5" in r["analise"]


def test_analise_texto_longo_demais_cai_na_regra(tmp_path):
    longo = {"analise": "x" * 601}
    p = Falso("g1", longo)
    c, _ = _cadeia(tmp_path, p)
    r = mod.analisar("BBAS3", RESULTADOS, c)
    assert r["origem"] == "REGRA"


def test_rota_http(tmp_path, monkeypatch):
    from app.api import app
    from app.simulador import analisar as mod_sim

    def _analisar_fake(simbolo, resultados, cadeia):
        return {"analise": "ok", "modelo": "g1", "origem": "MODELO",
                "tokens_usados": 10, "em_cache": False}

    monkeypatch.setattr(mod_sim, "analisar", _analisar_fake)
    monkeypatch.setattr(mod_sim, "montar_cadeia", lambda *a: None)

    client = TestClient(app)
    resp = client.post("/simulador/analisar", json={
        "simbolo": "WEGE3",
        "resultados": [{"versao": "VALOR", "quintil": 1, "retorno_pct": 0.04}],
    })
    assert resp.status_code == 200
    assert resp.json()["analise"] == "ok"
