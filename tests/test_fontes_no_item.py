"""TASK-IA-14: o item que cita trecho leva a fonte e o texto citado, para o painel mostrar sem chamar o servico."""

from app.contexto import TrechoDeContexto
from app.modelos import NEGATIVO, NEUTRO, RISCO_ALTO, PedidoOpiniao
from app.orquestrador import opinar

import json

TRECHO = TrechoDeContexto("ativos/WEGE3#por-ano/2023", "Ano 2023: retorno 41,2%.", "conhecimento/ativos/WEGE3.md#por-ano")


class _P:
    nome = "m"

    def gerar(self, sistema, usuario, schema):
        return json.dumps({"opiniao": NEGATIVO, "risco": RISCO_ALTO, "justificativa": [
            {"evidencia_id": "regra_v1", "leitura": "O sinal aponta VENDA_VALUATION."},
            {"trecho_id": TRECHO.trecho_id, "leitura": "Em 2023 o retorno foi de 41,2%."}]})


class _C:
    def trechos(self, pedido):
        return [TRECHO]


def test_item_com_trecho_leva_fonte_e_texto_e_item_de_evidencia_nao():
    pedido = PedidoOpiniao(simbolo="WEGE3", data_pregao="2026-10-06", horizonte_pregoes=126,
                           evidencias=[{"id": "regra_v1", "rotulo": "Sinal", "valor": "VENDA_VALUATION", "direcao": -1}],
                           permitidas=[NEGATIVO, NEUTRO], risco_calculado=RISCO_ALTO)
    r = opinar(pedido, _P(), "skills@x", contexto=_C())
    ev, tr = r.justificativa
    assert ev.fonte is None and ev.trecho is None
    assert tr.fonte == TRECHO.fonte and tr.trecho == TRECHO.texto
    assert r.fontes == [TRECHO.fonte]
