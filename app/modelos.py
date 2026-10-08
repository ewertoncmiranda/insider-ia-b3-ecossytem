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


# --- CTR-IA-01 v1.1 (SPEC 13.3): os 3 horizontes de um ativo numa chamada -------------------


class PedidoHorizonte(BaseModel):
    """Um horizonte do pedido v1.1: mesmos campos e regras da v1.0, sem os do ativo."""

    horizonte_pregoes: int = Field(gt=0)
    evidencias: list[Evidencia]
    permitidas: list[str] = Field(min_length=1)
    risco_calculado: str
    motivo_sem_base: str | None = None


class PedidoOpiniaoAtivo(BaseModel):
    simbolo: str
    data_pregao: str
    # Balde de cota (SPEC 13.4); hoje so `lote`. O painel nao gera opiniao (TASK-IA-37 descartada).
    uso: Literal["lote"] = "lote"
    dados_ausentes: list[str] = Field(default_factory=list)
    versao_regra: str = ""
    horizontes: list[PedidoHorizonte] = Field(min_length=1, max_length=6)

    @field_validator("horizontes")
    @classmethod
    def _sem_repetir(cls, valor: list[PedidoHorizonte]) -> list[PedidoHorizonte]:
        vistos = [h.horizonte_pregoes for h in valor]
        if len(set(vistos)) != len(vistos):
            raise ValueError(f"horizonte repetido: {vistos}")
        return valor

    def do_horizonte(self, h: PedidoHorizonte) -> PedidoOpiniao:
        """Pedido v1.0 equivalente, para reusar validador, regra e contexto sem mudar nada deles."""
        return PedidoOpiniao(simbolo=self.simbolo, data_pregao=self.data_pregao,
                             horizonte_pregoes=h.horizonte_pregoes, evidencias=h.evidencias,
                             permitidas=h.permitidas, risco_calculado=h.risco_calculado,
                             motivo_sem_base=h.motivo_sem_base, dados_ausentes=self.dados_ausentes,
                             versao_regra=self.versao_regra)


class ItemOpiniaoAtivo(RespostaOpiniao):
    horizonte_pregoes: int


class CotaDaResposta(BaseModel):
    """`gemini_disponivel = false` avisa o worker que o resto do lote nao deve chamar o servico."""

    balde: str
    restante_hoje: int | None = None
    gemini_disponivel: bool = False


class RespostaOpiniaoAtivo(BaseModel):
    simbolo: str
    data_pregao: str
    modelo: str
    skills_versao: str
    itens: list[ItemOpiniaoAtivo]
    cota: CotaDaResposta
