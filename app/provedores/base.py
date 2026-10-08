"""Porta dos provedores de modelo: o que a cadeia e o orquestrador esperam de quem gera texto.

Desde 2026-10-08 o unico provedor e o Gemini (`app/provedores/gemini.py`); sem ele, a reserva e a regra.
"""

from __future__ import annotations

from typing import Protocol


class ErroDoProvedor(RuntimeError):
    pass


class ProvedorLLM(Protocol):
    nome: str

    def gerar(self, sistema: str, usuario: str, schema: dict) -> str: ...
