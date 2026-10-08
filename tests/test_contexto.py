"""TASK-IA-11: trechos de ficha no contexto, citacao por trecho_id validada e fontes na resposta."""

from __future__ import annotations

import json
from datetime import date

from app.contexto import MAXIMO_DE_TRECHOS, ContextoRag, TrechoDeContexto, limitar
from app.modelos import NEGATIVO, NEUTRO, RISCO_ALTO, PedidoOpiniao
from app.orquestrador import opinar
from app.prompt import montar_mensagem
from app.validador import validar

TRECHO = TrechoDeContexto("ativos/WEGE3#por-ano/2023", "Ano 2023: retorno 41,2%, drawdown 18,5%.",
                          "conhecimento/ativos/WEGE3.md#por-ano")


def _pedido() -> PedidoOpiniao:
    return PedidoOpiniao(
        simbolo="WEGE3", data_pregao="2026-10-06", horizonte_pregoes=126,
        evidencias=[{"id": "regra_v1", "rotulo": "Sinal quantitativo", "valor": "VENDA_VALUATION", "direcao": -1},
                    {"id": "margem", "rotulo": "Margem Graham (%)", "valor": "-458.8", "direcao": -1}],
        permitidas=[NEGATIVO, NEUTRO], risco_calculado=RISCO_ALTO)


def _resposta(*itens):
    return {"opiniao": NEGATIVO, "risco": RISCO_ALTO, "justificativa": list(itens)}


EV = {"evidencia_id": "regra_v1", "leitura": "O sinal aponta VENDA_VALUATION."}


class _Contexto:
    def __init__(self, trechos):
        self._trechos = trechos

    def trechos(self, pedido):
        return self._trechos


class _Provedor:
    nome = "m"

    def __init__(self, resposta):
        self._r = resposta
        self.mensagens = []

    def gerar(self, sistema, usuario, schema):
        self.mensagens.append(usuario)
        return json.dumps(self._r)


def test_citar_trecho_existente_e_valido_e_numero_do_trecho_e_aceito():
    r = _resposta(EV, {"trecho_id": TRECHO.trecho_id, "leitura": "Em 2023 o retorno foi de 41,2% com queda máxima de 18,5%."})
    ok, erros = validar(r, _pedido(), [TRECHO])
    assert erros == [] and ok["justificativa"][1] == {"trecho_id": TRECHO.trecho_id, "leitura": r["justificativa"][1]["leitura"]}


def test_trecho_que_nao_foi_dado_e_rejeitado():
    r = _resposta(EV, {"trecho_id": "ativos/PETR4#por-ano/2020", "leitura": "Algo."})
    assert any("trecho inexistente" in e for e in validar(r, _pedido(), [TRECHO])[1])
    assert any("trecho inexistente" in e for e in validar(r, _pedido(), None)[1])


def test_numero_que_nao_esta_no_trecho_citado_e_rejeitado():
    r = _resposta(EV, {"trecho_id": TRECHO.trecho_id, "leitura": "Em 2023 o retorno foi de 77,7%."})
    assert any("número fora do trecho" in e for e in validar(r, _pedido(), [TRECHO])[1])


def test_citar_so_trecho_nao_basta_para_opiniao_direcional():
    r = _resposta({"trecho_id": TRECHO.trecho_id, "leitura": "Em 2023 o retorno foi de 41,2%."})
    assert any("sem citar evidência desfavorável" in e for e in validar(r, _pedido(), [TRECHO])[1])


def test_orquestrador_envia_trechos_e_devolve_as_fontes_citadas():
    resposta = _resposta(EV, {"trecho_id": TRECHO.trecho_id, "leitura": "Em 2023 o retorno foi de 41,2%."})
    provedor = _Provedor(resposta)
    r = opinar(_pedido(), provedor, "skills@x", contexto=_Contexto([TRECHO]))
    assert r.origem == "MODELO" and r.fontes == [TRECHO.fonte]
    assert TRECHO.trecho_id in provedor.mensagens[0]


def test_sem_contexto_tudo_funciona_como_antes_e_fontes_fica_vazio():
    r = opinar(_pedido(), _Provedor(_resposta(EV)), "skills@x", contexto=_Contexto([]))
    assert r.origem == "MODELO" and r.fontes == []


def test_trecho_inventado_pelo_modelo_cai_na_regra():
    ruim = _resposta(EV, {"trecho_id": "inventado#x", "leitura": "Algo."})
    r = opinar(_pedido(), _Provedor(ruim), "skills@x", contexto=_Contexto([TRECHO]))
    assert r.origem == "REGRA"


def test_limitar_remove_repetidos_vazios_e_corta():
    muitos = [TrechoDeContexto(f"t{i}", "x" * 900, "f") for i in range(8)]
    saida = limitar(muitos + [muitos[0], TrechoDeContexto("vazio", "  ", "f")])
    assert len(saida) == MAXIMO_DE_TRECHOS and all(len(t.texto) <= 600 for t in saida)


def test_mensagem_inclui_trechos_so_quando_ha():
    assert "trechos" not in json.loads(montar_mensagem(_pedido()))
    assert json.loads(montar_mensagem(_pedido(), [TRECHO]))["trechos"][0]["trecho_id"] == TRECHO.trecho_id


def test_contexto_rag_sem_modulo_ou_indice_devolve_vazio(tmp_path):
    pedido = _pedido()
    assert ContextoRag(tmp_path / "nao-existe.sqlite").trechos(pedido) == []
    assert date.fromisoformat(pedido.data_pregao).year == 2026
