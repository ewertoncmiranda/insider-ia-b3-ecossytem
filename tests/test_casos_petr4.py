"""TASK-IA-06: as falhas vistas em PETR4/2026-10-06, com os dossies reais do conjunto de avaliacao.

Falhas observadas no gerador antigo (antes do prompt 1.2):
1. contradicao sinal x evidencia: SINAL_POSITIVO justificado com a reversao a media (VENDA_TECNICA);
2. ids de fator em "o que invalida" (ex.: "fator_volatilidade_12m");
3. excesso de justificativas (mais de 5 itens).
Cada uma tem de ser rejeitada; a regra e uma resposta correta do modelo tem de passar.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.modelos import PedidoOpiniao
from app.regras import resposta_de_regra
from app.validador import validar

DOSSIES = Path(__file__).resolve().parents[1] / "avaliacao" / "dossies" / "2026-10-06.jsonl"


def _petr4() -> dict[int, PedidoOpiniao]:
    linhas = (json.loads(l) for l in DOSSIES.read_text(encoding="utf-8").splitlines() if l.strip())
    return {d["horizonte_pregoes"]: PedidoOpiniao(**d) for d in linhas if d["simbolo"] == "PETR4"}


PETR4 = _petr4()


def item(evidencia_id: str, leitura: str = "Indica leitura favorável no período.") -> dict:
    return {"evidencia_id": evidencia_id, "leitura": leitura}


def resposta(pedido: PedidoOpiniao, justificativa: list[dict], **extra) -> dict:
    return {"opiniao": "SINAL_POSITIVO", "risco": pedido.risco_calculado, "justificativa": justificativa, **extra}


def test_os_tres_horizontes_estao_no_conjunto():
    assert sorted(PETR4) == [21, 63, 126]


@pytest.mark.parametrize("horizonte", [21, 63, 126])
def test_regra_passa_no_validador(horizonte):
    pedido = PETR4[horizonte]
    regra = resposta_de_regra(pedido)
    # `o_que_invalida` nunca vem do modelo: o validador o recalcula e tem de dar o mesmo da regra
    normal, erros = validar({k: v for k, v in regra.items() if k != "o_que_invalida"}, pedido)
    assert erros == []
    assert normal["o_que_invalida"] == regra["o_que_invalida"]
    assert all(pedido.evidencias[[e.id for e in pedido.evidencias].index(j["evidencia_id"])].direcao > 0
               for j in normal["justificativa"])


@pytest.mark.parametrize("horizonte", [21, 63])
def test_resposta_correta_passa_e_a_reversao_vai_para_o_que_invalida(horizonte):
    pedido = PETR4[horizonte]
    normal, erros = validar(resposta(pedido, [item("fator_momento_12_1"), item("fator_drawdown_12m")]), pedido)
    assert erros == []
    assert normal["o_que_invalida"] == [
        "Há evidência em sentido contrário: sinal técnico de reversão à média (VENDA_TECNICA)."]


@pytest.mark.parametrize("horizonte", [21, 63])
def test_falha_1_positivo_justificado_com_evidencia_contraria(horizonte):
    pedido = PETR4[horizonte]
    _, erros = validar(resposta(pedido, [item("fator_momento_12_1"),
                                         item("sinal_reversao", "Reversão à média em venda técnica.")]), pedido)
    assert erros == ["SINAL_POSITIVO justificado com evidência contrária: ['sinal_reversao']"]
    _, erros = validar(resposta(pedido, [item("sinal_reversao", "Reversão à média em venda técnica.")]), pedido)
    assert "SINAL_POSITIVO sem citar evidência favorável" in erros


@pytest.mark.parametrize("invalida", [["fator_volatilidade_12m"], ["Se o sinal_reversao virar compra técnica."],
                                      ["Se a queda do pico em 12 meses aumentar."]])
def test_falha_2_ids_ou_evidencias_em_o_que_invalida(invalida):
    pedido = PETR4[21]
    _, erros = validar(resposta(pedido, [item("fator_momento_12_1")], o_que_invalida=invalida), pedido)
    assert any("o_que_invalida" in e for e in erros)


def test_falha_3_excesso_de_justificativas():
    pedido = PETR4[63]
    favoraveis = [e.id for e in pedido.evidencias if e.direcao > 0]
    assert len(favoraveis) > 5
    _, erros = validar(resposta(pedido, [item(i) for i in favoraveis]), pedido)
    assert erros == ["justificativa: no máximo 5 itens"]
    _, erros = validar(resposta(pedido, [item(i) for i in favoraveis[:5]]), pedido)
    assert erros == []


def test_longo_prazo_sem_evidencia_contraria_nao_tem_o_que_invalida():
    pedido = PETR4[126]
    normal, erros = validar(resposta(pedido, [item("fator_roic"), item("fator_earnings_yield")]), pedido)
    assert erros == [] and normal["o_que_invalida"] == []
