"""TASK-IA-05: o conjunto fixo (315 dossies de 2026-10-06) nao pode regredir (NFR-IA-05)."""

from __future__ import annotations

from avaliacao.rodar import carregar, rodar


def test_conjunto_tem_os_315_dossies_de_2026_10_06():
    assert len(carregar("2026-10-06")) == 315


def test_reserva_por_regra_reproduz_o_esperado_e_todo_esperado_e_valido():
    metricas = rodar("regra")
    assert metricas["total"] >= 315
    assert metricas["divergentes_da_regra"] == 0
    assert metricas["invalidos_no_validador"] == 0
