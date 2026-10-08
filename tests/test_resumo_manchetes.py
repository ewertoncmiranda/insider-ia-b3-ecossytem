"""TASK-IA-38: POST /manchetes/resumo com provedor falso e governador de verdade."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.cota import GovernadorCota
from app.manchetes import resumo as mod
from app.provedores.cadeia import GEMINI, Cadeia, Elo
from app.provedores.base import ErroDoProvedor

MANCHETES = [
    {"titulo": "Petrobras anuncia dividendos", "link": "https://n.test/1", "fonte": "Valor", "simbolos": ["PETR4"]},
    {"titulo": "Petrobras e o preço do diesel", "link": "https://n.test/2", "fonte": "Folha", "simbolos": ["petr4"]},
    {"titulo": "WEG compra fábrica", "link": "https://n.test/3", "fonte": "Exame", "simbolos": ["WEGE3"]},
    {"titulo": "Vale e o minério", "link": "https://n.test/4", "fonte": "Valor", "simbolos": ["VALE3"]},
]

BOA = {"topicos": [
    {"texto": "Petrobras: dividendos e diesel no noticiário.", "links": ["https://n.test/1", "https://n.test/2"]},
    {"texto": "WEG anunciou compra de fábrica.", "links": ["https://n.test/3"]},
    {"texto": "Vale acompanha o minério.", "links": ["https://n.test/4"]},
]}


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


def cadeia(tmp_path, *provedores):
    gov = GovernadorCota(tmp_path / "cota.sqlite", {p.nome: (15, 500) for p in provedores})
    return Cadeia([Elo(GEMINI, p) for p in provedores], gov), gov


def entrada(lista=MANCHETES):
    return mod._entrada([mod.Manchete(**m) for m in lista])


def test_tres_topicos_do_modelo_e_segunda_chamada_do_dia_nao_gasta_cota(tmp_path):
    p = Falso("g1", BOA)
    c, gov = cadeia(tmp_path, p)
    r1 = mod.resumir(entrada(), c)
    assert (r1["origem"], r1["modelo"], r1["em_cache"]) == ("MODELO", "g1", False)
    assert len(r1["topicos"]) == 3
    r2 = mod.resumir(entrada(list(reversed(MANCHETES))), c)  # mesma entrada em outra ordem
    assert r2["em_cache"] is True and r2["topicos"] == r1["topicos"]
    assert p.chamadas == 1
    assert gov.estado_modelos()[0]["usadas_hoje"] == 1


def test_link_fora_da_entrada_rejeita_e_passa_ao_proximo(tmp_path):
    inventado = {"topicos": [dict(t) for t in BOA["topicos"]]}
    inventado["topicos"][1] = {"texto": "WEG em alta.", "links": ["https://outro.test/x"]}
    p1, p2 = Falso("g1", inventado), Falso("g2", BOA)
    r = mod.resumir(entrada(), cadeia(tmp_path, p1, p2)[0])
    assert r["modelo"] == "g2"
    assert mod.validar(inventado, entrada()) == ["tópico 2: link fora da entrada (1)"]


@pytest.mark.parametrize("ruim, erro", [
    ({"topicos": BOA["topicos"][:2]}, "2 tópicos (esperado 3)"),
    ({"topicos": [*BOA["topicos"][:2], {"texto": "x", "links": []}]}, "tópico 3: sem link"),
    ({"topicos": [*BOA["topicos"][:2], {"texto": "Retorno garantido", "links": ["https://n.test/4"]}]},
     "tópico 3: vocabulário proibido"),
    ({"x": 1}, "sem lista de tópicos"),
])
def test_validacao(ruim, erro):
    assert erro in mod.validar(ruim, entrada())


def test_tudo_falhou_vira_regra_sem_cache(tmp_path):
    p = Falso("g1", ErroDoProvedor("429"), "não é json")
    c, _ = cadeia(tmp_path, p)
    r = mod.resumir(entrada(), c)
    assert (r["origem"], r["modelo"]) == ("REGRA", "regra")
    assert r["topicos"][0] == {"texto": "PETR4: Petrobras anuncia dividendos (+1 manchete)",
                               "links": ["https://n.test/1", "https://n.test/2"]}
    assert len(r["topicos"]) == 3
    assert mod.validar(r, entrada()) == []  # a regra tambem respeita o contrato
    assert mod.resumir(entrada(), c)["em_cache"] is False  # regra nao vai para o cache


def test_poucas_manchetes_e_entrada_vazia(tmp_path):
    uma = entrada(MANCHETES[2:3])
    assert mod.topicos_de_regra(uma) == [{"texto": "WEGE3: WEG compra fábrica", "links": ["https://n.test/3"]}]
    assert mod.validar({"topicos": [BOA["topicos"][1]]}, uma) == []
    assert mod.resumir([], None)["topicos"] == []


def test_entrada_limita_a_30_e_tira_link_repetido():
    muitas = [{"titulo": f"n{i}", "link": f"https://n.test/{i % 35}"} for i in range(40)]
    assert len(entrada(muitas)) == 30
    assert len({m["link"] for m in entrada(muitas)}) == 30


def test_rota_sem_provedor_responde_por_regra(monkeypatch):
    from app.api import app

    monkeypatch.setattr(mod, "montar_cadeia", lambda settings, uso: None)
    r = TestClient(app).post("/manchetes/resumo", json={"manchetes": MANCHETES})
    assert r.status_code == 200
    assert r.json()["origem"] == "REGRA" and len(r.json()["topicos"]) == 3
    assert TestClient(app).post("/manchetes/resumo", json={"manchetes": [{"link": "x"}]}).status_code == 422
