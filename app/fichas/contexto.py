"""Derivados comuns a todas as fichas, calculados uma vez. Puro."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.fichas import precos
from app.fichas.banco import BaseDeDados


@dataclass
class Contexto:
    base: BaseDeDados
    ajustadas: dict[str, precos.Serie]
    retornos: dict[str, dict[date, float]]        # limpos (sem saltos suspeitos)
    saltos: dict[str, list[date]]
    mercado: dict[date, float]                    # igual peso, papeis liquidos
    mercado_por_ano: dict[int, float | None]

    def setor(self, simbolo: str) -> str | None:
        return self.base.empresa.get(simbolo, (None, None, None))[2]

    def grupo(self, simbolo: str) -> str | None:
        setor = self.setor(simbolo)
        return self.base.grupo_setor.get(setor) if setor else None


def montar(base: BaseDeDados) -> Contexto:
    ajustadas, retornos, saltos = {}, {}, {}
    for simbolo, serie in base.precos.items():
        eventos = [(d, fator) for d, fator, _, _ in base.eventos.get(simbolo, [])]
        ajustadas[simbolo] = precos.ajustar(serie, eventos)
        brutos = precos.retornos_diarios(ajustadas[simbolo])
        saltos[simbolo] = precos.saltos(brutos)
        retornos[simbolo] = precos.limpos(brutos)
    mercado = precos.mercado_igual_peso(retornos)
    mercado_por_ano = {ano: precos.composto(rs) for ano, rs in precos.por_ano(mercado).items()}
    return Contexto(base, ajustadas, retornos, saltos, mercado, mercado_por_ano)
