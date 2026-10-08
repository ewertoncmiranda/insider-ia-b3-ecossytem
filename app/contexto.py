"""Contexto do pedido (SPEC 6.5, TASK-IA-11): trechos de fichas com fonte, filtrados por ponto no tempo.

`FonteDeContexto` e a porta; `ContextoRag` e o adaptador sobre `app.rag` (busca por metadado + busca
textual/vetorial, TASK-IA-10). Sem indice ou sem `app.rag`, o contexto e vazio e o servico segue so com
as evidencias do dia. Nada daqui levanta excecao para o chamador.

P-4 (ponto no tempo): so entram trechos com `disponivel_ate <= data_pregao` do pedido; quem filtra e a
busca, que recebe a data como filtro duro.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Protocol

from app.modelos import PedidoOpiniao

log = logging.getLogger("ia-opiniao")

MAXIMO_DE_TRECHOS = 4
MAXIMO_DE_CARACTERES_POR_TRECHO = 600
# ~2 a 4 mil tokens no total (SPEC 6.5): 4 trechos x 600 caracteres ficam bem abaixo.


@dataclass(frozen=True)
class TrechoDeContexto:
    trecho_id: str
    texto: str
    fonte: str


class FonteDeContexto(Protocol):
    def trechos(self, pedido: PedidoOpiniao) -> list[TrechoDeContexto]: ...


def limitar(trechos: list[TrechoDeContexto]) -> list[TrechoDeContexto]:
    """Sem repetir trecho_id, no maximo MAXIMO_DE_TRECHOS, texto cortado no limite."""
    vistos: set[str] = set()
    saida: list[TrechoDeContexto] = []
    for t in trechos:
        if t.trecho_id in vistos or not t.texto.strip():
            continue
        vistos.add(t.trecho_id)
        saida.append(TrechoDeContexto(t.trecho_id, t.texto.strip()[:MAXIMO_DE_CARACTERES_POR_TRECHO], t.fonte))
        if len(saida) == MAXIMO_DE_TRECHOS:
            break
    return saida


class ContextoRag:
    """Passo 1: leitura direta por metadado (resumo do ativo e do setor); passo 2: busca por tema."""

    def __init__(self, indice: Path | None = None):
        self._indice = indice

    def trechos(self, pedido: PedidoOpiniao) -> list[TrechoDeContexto]:
        try:
            from app.rag.busca import buscar, por_metadado  # noqa: PLC0415 - adaptador opcional
        except ImportError:
            return []
        try:
            data = date.fromisoformat(pedido.data_pregao)
            achados = por_metadado(disponivel_ate=data, simbolo=pedido.simbolo, secoes=("resumo",),
                                   indice=self._indice)
            consulta = " ".join(e.rotulo for e in pedido.evidencias if e.direcao != 0)[:200]
            if consulta:
                achados += buscar(consulta, disponivel_ate=data, simbolo=pedido.simbolo,
                                  k=MAXIMO_DE_TRECHOS, indice=self._indice)
        except Exception as erro:  # noqa: BLE001 - indice ausente/corrompido nao pode derrubar /opiniao
            log.warning("contexto indisponivel para %s: %s", pedido.simbolo, erro)
            return []
        return limitar([TrechoDeContexto(t.trecho_id, t.texto, t.fonte) for t in achados])
