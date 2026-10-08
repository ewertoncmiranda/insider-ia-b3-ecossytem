"""Cadeia de provedores (TASK-IA-26, SPEC 13.2): tenta na ordem de `PROVEDORES_*` e passa ao proximo.

A cadeia so sabe *chamar*: consulta o governador de cota antes de cada chamada ao Gemini e avisa
quando o Gemini recusa por cota (429). Quem valida a resposta e decide passar ao proximo e o
orquestrador, porque so ele sabe o que e resposta valida (e, no v1.1, por horizonte).

Pecas que outras tarefas trazem e que aqui entram por interface:
- o provedor Gemini (TASK-IA-24, `app/provedores/gemini.py`, classe `GeminiProvedor`);
- o governador de cota (TASK-IA-25, `app/cota.py`, `GovernadorCota`). Sem ele, `SemGovernador` libera tudo.

O 429 e reconhecido pelos atributos `espera_s`/`diaria` do `ErroDeCota` do provedor Gemini.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Protocol

from app.provedores.ollama import ErroDoProvedor, OllamaProvedor, ProvedorLLM

log = logging.getLogger("ia-opiniao")

GEMINI, OLLAMA = "gemini", "ollama"


class Governador(Protocol):
    """Porta do governador de cota: a interface de `app/cota.py` (GovernadorCota, TASK-IA-25)."""

    def reservar(self, balde: str, modelo: str) -> Any:
        """Debita uma chamada se houver cota e o modelo nao estiver em pausa. Devolve `bool` ou
        um objeto com `.permitido` (a `Decisao` do GovernadorCota)."""
        ...

    def pausar(self, modelo: str, espera_s: float | None = None, diaria: bool = False) -> Any:
        """O Gemini respondeu 429: pausa o modelo pelo tempo pedido (ou ate zerar o dia)."""
        ...

    def gemini_disponivel(self, balde: str) -> bool: ...

    def restante(self, balde: str) -> int | None: ...


class SemGovernador:
    """Sem `app/cota.py` neste build: nao limita nada e so registra a recusa no log."""

    def reservar(self, balde: str, modelo: str) -> bool:
        return True

    def pausar(self, modelo: str, espera_s: float | None = None, diaria: bool = False) -> None:
        log.warning("cota recusada modelo=%s espera_s=%s diaria=%s (sem governador)", modelo, espera_s, diaria)

    def gemini_disponivel(self, balde: str) -> bool:
        return True

    def restante(self, balde: str) -> int | None:
        return None


def _permitido(decisao: Any) -> bool:
    return bool(getattr(decisao, "permitido", decisao))


def _e_recusa_de_cota(erro: BaseException) -> bool:
    """O `ErroDeCota` do provedor Gemini (TASK-IA-24) traz `espera_s` e `diaria`."""
    return hasattr(erro, "espera_s") and hasattr(erro, "diaria")

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
        if elo.tipo == GEMINI and not _permitido(self.governador.reservar(balde, elo.nome)):
            raise ErroDoProvedor(f"{elo.nome}: sem cota no balde {balde} ou em pausa")
        try:
            return elo.provedor.gerar(sistema, usuario, schema)
        except ErroDoProvedor as erro:
            if elo.tipo == GEMINI and _e_recusa_de_cota(erro):
                self.governador.pausar(elo.nome, erro.espera_s, erro.diaria)
            raise


def como_cadeia(provedor: ProvedorLLM | Cadeia | None) -> Cadeia | None:
    """Aceita um provedor solto (testes e chamadas antigas): vira uma cadeia de um elo, com a segunda
    tentativa de sempre."""
    if provedor is None or isinstance(provedor, Cadeia):
        return provedor
    return Cadeia([Elo(OLLAMA, provedor, segunda_tentativa=True)])


def _provedores_gemini(settings) -> list[ProvedorLLM]:
    """Um GeminiProvedor por modelo (TASK-IA-24), se o modulo existir neste build; senao nenhum."""
    try:
        from app.provedores.gemini import criar_provedores  # noqa: PLC0415 - modulo da TASK-IA-24
    except ImportError:
        return []
    try:
        return list(criar_provedores(settings.gemini_api_key, settings.gemini_modelos,
                                     timeout_s=getattr(settings, "gemini_timeout_s", 30)))
    except Exception as erro:  # noqa: BLE001 - SDK ausente ou chave invalida: Gemini fica de fora
        log.warning("Gemini fora da cadeia: %s", type(erro).__name__)
        return []


_GOVERNADOR: Governador | None = None


def governador_padrao(settings) -> Governador:
    """GovernadorCota (TASK-IA-25) unico por processo, no volume do indice; sem o modulo, SemGovernador."""
    global _GOVERNADOR  # noqa: PLW0603 - uma conexao SQLite por processo
    if _GOVERNADOR is None:
        try:
            from app.cota import GovernadorCota  # noqa: PLC0415 - modulo da TASK-IA-25
            limites = [(m, (lim.rpm, lim.rpd)) for m, lim in zip(settings.gemini_modelos, settings.gemini_limites)]
            pct = {"chat": settings.cota_chat_pct, "card": settings.cota_card_pct, "lote": settings.cota_lote_pct}
            _GOVERNADOR = GovernadorCota(settings.rag_indice.parent / "cota.sqlite", limites, pct=pct)
        except Exception as erro:  # noqa: BLE001 - modulo ausente, tzdata faltando, volume sem escrita
            log.warning("governador de cota indisponivel (%s); sem limite local", type(erro).__name__)
            _GOVERNADOR = SemGovernador()
    return _GOVERNADOR

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
            elos.extend(Elo(GEMINI, p) for p in _provedores_gemini(settings))
    if not elos:
        return None
    if governador is None:
        governador = governador_padrao(settings) if any(e.tipo == GEMINI for e in elos) else SemGovernador()
    return Cadeia(elos, governador)
