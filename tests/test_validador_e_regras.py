"""TASK-IA-02/06: validador, reserva por regra e orquestrador (portados do gerar-insights, sem rede)."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app import api
from app.modelos import (
    NEGATIVO,
    NEUTRO,
    POSITIVO,
    RISCO_ALTO,
    RISCO_MEDIO,
    SEM_BASE,
    PedidoOpiniao,
)
from app.orquestrador import opinar
from app.provedores.ollama import ErroDoProvedor
from app.regras import resposta_de_regra
from app.validador import validar


def _pedido(permitidas=(NEGATIVO, NEUTRO), risco=RISCO_ALTO, evidencias=None, **extra) -> PedidoOpiniao:
    evidencias = evidencias if evidencias is not None else [
        {"id": "regra_v1", "rotulo": "Sinal quantitativo determinístico (valuation)",
         "valor": "VENDA_VALUATION", "direcao": -1},
        {"id": "margem_graham_base", "rotulo": "Margem de segurança (Graham, cenário base, %)",
         "valor": "-458.8", "direcao": -1},
        {"id": "sinal_momentum", "rotulo": "Sinal técnico de momentum", "valor": "NEUTRO_TECNICO",
         "direcao": 0},
    ]
    return PedidoOpiniao(simbolo="WEGE3", data_pregao="2026-10-06", horizonte_pregoes=63,
                         evidencias=evidencias, permitidas=list(permitidas), risco_calculado=risco,
                         versao_regra="2026.09.27-3", **extra)


def _resposta(**extra):
    base = {"opiniao": NEGATIVO, "risco": RISCO_ALTO,
            "justificativa": [{"evidencia_id": "regra_v1",
                               "leitura": "O sinal determinístico aponta VENDA_VALUATION."}]}
    base.update(extra)
    return base


class TestValidador:
    def test_resposta_correta_passa_e_invalida_vem_das_evidencias(self):
        ok, erros = validar(_resposta(), _pedido(evidencias=[
            {"id": "regra_v1", "rotulo": "Sinal", "valor": "VENDA_VALUATION", "direcao": -1},
            {"id": "mom", "rotulo": "Momentum", "valor": "COMPRA_TECNICA", "direcao": 1}]))
        assert erros == []
        assert ok["o_que_invalida"] == ["Há evidência em sentido contrário: momentum (COMPRA_TECNICA)."]

    def test_opiniao_fora_das_permitidas(self):
        assert any("fora das permitidas" in e for e in validar(_resposta(opiniao=POSITIVO), _pedido())[1])

    def test_risco_diferente_do_calculado(self):
        assert any("difere do calculado" in e for e in validar(_resposta(risco=RISCO_MEDIO), _pedido())[1])

    def test_evidencia_inexistente(self):
        r = _resposta(justificativa=[{"evidencia_id": "inventada", "leitura": "x"}])
        assert any("inexistente" in e for e in validar(r, _pedido())[1])

    def test_numero_fora_do_dossie(self):
        r = _resposta(justificativa=[{"evidencia_id": "margem_graham_base",
                                      "leitura": "A margem é de 73,2% segundo o modelo."}])
        assert any("número fora do dossiê" in e for e in validar(r, _pedido())[1])

    def test_numero_do_dossie_e_aceito(self):
        r = _resposta(justificativa=[{"evidencia_id": "margem_graham_base",
                                      "leitura": "A margem de segurança está em -458.8%, bem negativa."}])
        assert validar(r, _pedido())[1] == []

    def test_vocabulario_proibido(self):
        r = _resposta(justificativa=[{"evidencia_id": "regra_v1", "leitura": "Queda garantida."}])
        assert any("vocabulário" in e for e in validar(r, _pedido())[1])

    def test_negativo_exige_evidencia_desfavoravel_citada(self):
        r = _resposta(justificativa=[{"evidencia_id": "sinal_momentum", "leitura": "Momentum neutro."}])
        assert any("sem citar evidência desfavorável" in e for e in validar(r, _pedido())[1])

    def test_mais_de_cinco_justificativas(self):
        evid = [{"id": f"e{i}", "rotulo": f"Evidência {i}", "valor": "x", "direcao": -1} for i in range(6)]
        itens = [{"evidencia_id": f"e{i}", "leitura": "dado"} for i in range(6)]
        assert any("no máximo 5" in e for e in validar(_resposta(justificativa=itens),
                                                       _pedido(evidencias=evid))[1])

    def test_o_que_invalida_do_modelo_repetindo_evidencia_ou_id_e_rejeitado(self):
        p = _pedido()
        assert any("repete" in e for e in validar(_resposta(o_que_invalida=[f"{p.evidencias[0].rotulo}: x"]), p)[1])
        assert validar(_resposta(o_que_invalida=["fator_accruals e fator_beta_12m"]), p)[1]

    def test_nao_objeto(self):
        assert validar([], _pedido())[0] is None


class TestReservaPorRegra:
    def test_positivo_so_justifica_com_o_que_sustenta_e_move_o_contrario_para_invalida(self):
        evid = [{"id": "momento", "rotulo": "Momento 12m", "valor": "percentil 95", "direcao": 1},
                {"id": "drawdown", "rotulo": "Queda do pico", "valor": "percentil 90", "direcao": 1},
                {"id": "reversao", "rotulo": "Reversão à média", "valor": "VENDA_TECNICA", "direcao": -1}]
        p = _pedido(permitidas=(POSITIVO, NEUTRO), evidencias=evid)
        r = resposta_de_regra(p)
        assert [j["evidencia_id"] for j in r["justificativa"]] == ["momento", "drawdown"]
        assert r["o_que_invalida"] == ["Há evidência em sentido contrário: reversão à média (VENDA_TECNICA)."]
        assert validar({**r, "o_que_invalida": []}, p)[1] == []

    def test_sem_base_nao_inventa_direcao(self):
        r = resposta_de_regra(_pedido(permitidas=(SEM_BASE,), evidencias=[]))
        assert r["opiniao"] == SEM_BASE and r["justificativa"] == [] and r["o_que_invalida"] == []


class _Provedor:
    nome = "modelo-teste"

    def __init__(self, respostas):
        self._respostas = list(respostas)
        self.chamadas = 0

    def gerar(self, sistema, usuario, schema):
        self.chamadas += 1
        item = self._respostas.pop(0)
        if isinstance(item, Exception):
            raise item
        return item if isinstance(item, str) else json.dumps(item)


class TestOrquestrador:
    def test_modelo_valido_na_primeira(self):
        r = opinar(_pedido(), _Provedor([_resposta()]), "skills@x")
        assert r.origem == "MODELO" and r.tentativas == 1 and r.modelo == "modelo-teste"

    def test_segunda_tentativa_corrige_a_primeira(self):
        r = opinar(_pedido(), _Provedor([_resposta(opiniao=POSITIVO), _resposta()]), "skills@x")
        assert r.origem == "MODELO" and r.tentativas == 2

    def test_duas_rejeicoes_caem_na_regra(self):
        p = _Provedor(["isto nao e json", _resposta(opiniao=POSITIVO)])
        r = opinar(_pedido(), p, "skills@x")
        assert r.origem == "REGRA" and r.opiniao == NEGATIVO and p.chamadas == 2

    def test_provedor_fora_do_ar_cai_na_regra_sem_excecao(self):
        r = opinar(_pedido(), _Provedor([ErroDoProvedor("fora")]), "skills@x")
        assert r.origem == "REGRA"

    def test_so_sem_base_permitido_dispensa_o_modelo(self):
        provedor = _Provedor([])
        r = opinar(_pedido(permitidas=(SEM_BASE,), motivo_sem_base="dados críticos atrasados"), provedor, "skills@x")
        assert provedor.chamadas == 0 and r.opiniao == SEM_BASE and r.origem == "REGRA"
        assert "dados críticos atrasados" in r.dados_ausentes


class TestEndpoint:
    def test_post_opiniao_sem_ollama_devolve_200_pela_regra(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_URL", "http://127.0.0.1:1")
        corpo = _pedido().model_dump()
        resposta = TestClient(api.app).post("/opiniao", json=corpo)
        assert resposta.status_code == 200
        assert resposta.json()["origem"] == "REGRA" and resposta.json()["opiniao"] == NEGATIVO

    def test_pedido_com_opiniao_fora_do_vocabulario_e_422(self):
        corpo = _pedido().model_dump()
        corpo["permitidas"] = ["COMPRA"]
        assert TestClient(api.app).post("/opiniao", json=corpo).status_code == 422
