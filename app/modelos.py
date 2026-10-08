"""Contrato CTR-IA-01 (SPEC 5.1): entrada, saida e vocabulario fechado.

O vocabulario e igual aos CHECK da migration V22 (`opiniao_ia`); mudar aqui exige migration nova.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

POSITIVO = "SINAL_POSITIVO"
NEGATIVO = "SINAL_NEGATIVO"
NEUTRO = "SINAL_NEUTRO"
SEM_BASE = "SEM_BASE"
OPINIOES: tuple[str, ...] = (POSITIVO, NEGATIVO, NEUTRO, SEM_BASE)

RISCO_BAIXO, RISCO_MEDIO, RISCO_ALTO = "RISCO_BAIXO", "RISCO_MEDIO", "RISCO_ALTO"
RISCOS: tuple[str, ...] = (RISCO_BAIXO, RISCO_MEDIO, RISCO_ALTO)

ORIGEM_MODELO, ORIGEM_REGRA = "MODELO", "REGRA"


class Evidencia(BaseModel):
    id: str
    rotulo: str
    valor: str
    direcao: Literal[-1, 0, 1]


class PedidoOpiniao(BaseModel):
    """Entrada: o `gerar-insights` e dono das evidencias, das opinioes permitidas e do risco."""

    simbolo: str
    data_pregao: str
    horizonte_pregoes: int = Field(gt=0)
    evidencias: list[Evidencia]
    permitidas: list[str] = Field(min_length=1)
    risco_calculado: str
    motivo_sem_base: str | None = None
    dados_ausentes: list[str] = Field(default_factory=list)
    versao_regra: str = ""

    @field_validator("permitidas")
    @classmethod
    def _so_vocabulario(cls, valor: list[str]) -> list[str]:
        fora = [v for v in valor if v not in OPINIOES]
        if fora:
            raise ValueError(f"opinioes fora do vocabulario: {fora}")
        return valor

    @field_validator("risco_calculado")
    @classmethod
    def _risco_valido(cls, valor: str) -> str:
        if valor not in RISCOS:
            raise ValueError(f"risco fora do vocabulario: {valor}")
        return valor


class ItemDeJustificativa(BaseModel):
    """Cita `evidencia_id` (numero do dia) ou `trecho_id` (RAG, TASK-IA-11)."""

    evidencia_id: str | None = None
    trecho_id: str | None = None
    leitura: str
    # So em item com trecho_id: caminho da ficha (`conhecimento/...md#secao`) e o texto citado, copiados
    # na hora da geracao. O painel mostra a fonte sem precisar alcançar este servico (rede `ia` interna).
    fonte: str | None = None
    trecho: str | None = None


class RespostaOpiniao(BaseModel):
    opiniao: str
    risco: str
    justificativa: list[ItemDeJustificativa]
    o_que_invalida: list[str]
    dados_ausentes: list[str]
    fontes: list[str] = Field(default_factory=list)
    modelo: str
    skills_versao: str
    origem: str
    tentativas: int = 0
