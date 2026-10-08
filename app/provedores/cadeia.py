"""Cadeia de provedores (TASK-IA-26, SPEC 13.2): tenta na ordem de `PROVEDORES_*` e passa ao proximo.

A cadeia so sabe *chamar*: consulta o governador de cota antes de cada chamada ao Gemini e avisa
quando o Gemini recusa por cota (429). Quem valida a resposta e decide passar ao proximo e o
orquestrador, porque so ele sabe o que e resposta valida (e, no v1.1, por horizonte).

Pecas que outras tarefas trazem e que aqui entram por interface:
- o provedor Gemini (TASK-IA-24, `app/provedores/gemini.py`, classe `GeminiProvedor`);
- o governador de cota (TASK-IA-25, `app/cota.py`). Sem ele, `SemGovernador` libera tudo.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Protocol

from app.provedores.ollama import ErroDoProvedor, OllamaProvedor, ProvedorLLM

log = logging.getLogger("ia-opiniao")

GEMINI, OLLAMA = "gemini", "ollama"


class ErroDeCota(ErroDoProvedor):
    """Provedor recusou por cota (HTTP 429). `diaria` = a cota do dia acabou, nao so a do minuto."""

    def __init__(self, mensagem: str, espera_s: float | None = None, diaria: bool = False):
        super().__init__(mensagem)
        self.espera_s = espera_s
        self.diaria = diaria


class Governador(Protocol):
    """Porta do governador de cota (TASK-IA-25)."""

    def reservar(self, modelo: str, balde: str) -> bool:
        """Debita uma chamada do modelo no balde se houver cota e o modelo nao estiver em pausa."""
        ...

    def registrar_recusa(self, modelo: str, espera_s: float | None, diaria: bool) -> None:
        """O Gemini respondeu 429: pausa o modelo pelo tempo pedido (ou ate zerar o dia)."""
        ...

    def disponivel(self, modelo: str, balde: str) -> bool:
        """Consulta sem debitar: o modelo ainda pode ser chamado neste balde hoje?"""
        ...

    def restante(self, balde: str) -> int | None:
        """Chamadas que ainda cabem no balde hoje; None quando nao ha contagem."""
        ...


class SemGovernador:
    """Enquanto a TASK-IA-25 nao existe: nao limita nada e so registra a recusa no log."""

    def reservar(self, modelo: str, balde: str) -> bool:
        return True

    def registrar_recusa(self, modelo: str, espera_s: float | None, diaria: bool) -> None:
        log.warning("cota recusada modelo=%s espera_s=%s diaria=%s (sem governador)", modelo, espera_s, diaria)

    def disponivel(self, modelo: str, balde: str) -> bool:
        return True

    def restante(self, balde: str) -> int | None:
        return None


@dataclass(frozen=True)
class Elo:
    """Um provedor da cadeia. `segunda_tentativa`: refazer com os erros da primeira (so o local;
    no Gemini custaria outra chamada de cota, SPEC 13.6)."""

    tipo: str
    provedor: ProvedorLLM
    segunda_tentativa: bool = False

    @property
    def nome(self) -> str:
        return self.provedor.nome


@dataclass
class Cadeia:
    elos: list[Elo]
    governador: Governador = field(default_factory=SemGovernador)

    @property
    def nome(self) -> str:
        """Nome do primeiro elo (identidade padrao quando ninguem respondeu)."""
        return self.elos[0].nome if self.elos else "regra"

    def chamar(self, elo: Elo, balde: str, sistema: str, usuario: str, schema: dict) -> str:
        """Uma chamada a um elo. Levanta ErroDoProvedor se nao houver cota ou se o provedor falhar."""
        if elo.tipo == GEMINI and not self.governador.reservar(elo.nome, balde):
            raise ErroDoProvedor(f"{elo.nome}: sem cota no balde {balde} ou em pausa")
        try:
            return elo.provedor.gerar(sistema, usuario, schema)
        except ErroDeCota as erro:
            self.governador.registrar_recusa(elo.nome, erro.espera_s, erro.diaria)
            raise


def como_cadeia(provedor: ProvedorLLM | Cadeia | None) -> Cadeia | None:
    """Aceita um provedor solto (testes e chamadas antigas): vira uma cadeia de um elo, com a segunda
    tentativa de sempre."""
    if provedor is None or isinstance(provedor, Cadeia):
        return provedor
    return Cadeia([Elo(OLLAMA, provedor, segunda_tentativa=True)])


def _provedor_gemini(settings, modelo: str) -> ProvedorLLM | None:
    """GeminiProvedor da TASK-IA-24, se ja existir neste build; senao o Gemini fica fora da cadeia."""
    try:
        from app.provedores.gemini import GeminiProvedor  # noqa: PLC0415 - modulo da TASK-IA-24
    except ImportError:
        return None
    return GeminiProvedor(api_key=settings.gemini_api_key, modelo=modelo,
                          timeout_s=getattr(settings, "gemini_timeout_s", 30))


def montar_cadeia(settings, uso: str = "lote", governador: Governador | None = None) -> Cadeia | None:
    """Cadeia na ordem de `PROVEDORES_LOTE` (lote e card) ou `PROVEDORES_CHAT` (chat).

    Gemini sem chave, sem modelos ou sem o modulo da IA-24 fica de fora (indisponivel, DEC-IA-09).
    Cada modelo de `GEMINI_MODELOS` vira um elo, na ordem: 429 no primeiro passa ao segundo.
    """
    ordem = getattr(settings, "provedores_chat" if uso == "chat" else "provedores_lote", (OLLAMA,))
    elos: list[Elo] = []
    for tipo in ordem:
        if tipo == OLLAMA:
            elos.append(Elo(OLLAMA, OllamaProvedor(settings.ollama_url, settings.modelo_chat,
                                                   timeout_s=settings.timeout_modelo_s), segunda_tentativa=True))
        elif tipo == GEMINI and getattr(settings, "gemini_configurado", False):
            for modelo in settings.gemini_modelos:
                provedor = _provedor_gemini(settings, modelo)
                if provedor is not None:
                    elos.append(Elo(GEMINI, provedor))
    if not elos:
        return None
    return Cadeia(elos, governador or SemGovernador())
