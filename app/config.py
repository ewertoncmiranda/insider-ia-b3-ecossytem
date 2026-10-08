"""Configuracao: toda variavel de ambiente do servico passa por aqui (fonte unica)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

PROVEDORES_VALIDOS = ("gemini", "ollama")
MODELOS_GEMINI_PADRAO = "gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-3.8-flash"
LIMITES_GEMINI_PADRAO = "15/500,15/500,5/20"


class ConfiguracaoInvalida(ValueError):
    """Variavel de ambiente com valor que o servico nao sabe usar (a mensagem nunca traz a chave)."""


@dataclass(frozen=True)
class LimiteDeModelo:
    """Limites do nivel gratuito de um modelo: requisicoes por minuto e por dia."""

    rpm: int
    rpd: int


def _lista(texto: str) -> tuple[str, ...]:
    return tuple(parte.strip() for parte in texto.split(",") if parte.strip())


def _inteiro(nome: str, padrao: str, minimo: int = 0) -> int:
    bruto = os.getenv(nome, padrao).strip()
    try:
        valor = int(bruto)
    except ValueError as erro:
        raise ConfiguracaoInvalida(f"{nome} deve ser um numero inteiro, recebeu {bruto!r}") from erro
    if valor < minimo:
        raise ConfiguracaoInvalida(f"{nome} deve ser pelo menos {minimo}, recebeu {valor}")
    return valor


def _limites(texto: str, quantidade: int, reserva: LimiteDeModelo) -> tuple[LimiteDeModelo, ...]:
    """`RPM/RPD` por modelo, na ordem de GEMINI_MODELOS. Menos itens que modelos: o resto usa a reserva."""
    itens = _lista(texto)
    if len(itens) > quantidade:
        raise ConfiguracaoInvalida(
            f"GEMINI_LIMITES tem {len(itens)} itens para {quantidade} modelo(s) em GEMINI_MODELOS")
    limites: list[LimiteDeModelo] = []
    for item in itens:
        rpm, separador, rpd = item.partition("/")
        try:
            limite = LimiteDeModelo(rpm=int(rpm), rpd=int(rpd))
        except ValueError as erro:
            raise ConfiguracaoInvalida(f"GEMINI_LIMITES: {item!r} nao esta no formato RPM/RPD") from erro
        if not separador or limite.rpm < 1 or limite.rpd < 1:
            raise ConfiguracaoInvalida(f"GEMINI_LIMITES: {item!r} precisa de RPM/RPD maiores que zero")
        limites.append(limite)
    return tuple(limites) + (reserva,) * (quantidade - len(limites))


def _provedores(nome: str, padrao: str) -> tuple[str, ...]:
    ordem = _lista(os.getenv(nome, padrao).lower())
    desconhecidos = [p for p in ordem if p not in PROVEDORES_VALIDOS]
    if desconhecidos:
        raise ConfiguracaoInvalida(f"{nome} tem provedor desconhecido: {', '.join(desconhecidos)}")
    return ordem


@dataclass(frozen=True)
class Settings:
    ollama_url: str
    modelo_chat: str
    modelo_embed: str
    vetores_url: str | None
    rag_indice: Path
    dir_skills: Path
    dir_conhecimento: Path
    timeout_modelo_s: int
    log_level: str
    # Gemini (SPEC 13.5, DEC-IA-09/10). A chave nunca aparece em repr, log, resposta ou /saude.
    gemini_api_key: str = field(default="", repr=False)
    gemini_modelos: tuple[str, ...] = ()
    gemini_limites: tuple[LimiteDeModelo, ...] = ()
    gemini_timeout_s: int = 30
    provedores_lote: tuple[str, ...] = ("gemini", "ollama")
    provedores_chat: tuple[str, ...] = ("gemini",)
    cota_chat_pct: int = 40
    cota_card_pct: int = 20
    cota_lote_pct: int = 40
    chat_max_dia_sessao: int = 60
    chat_intervalo_s: int = 3
    gestor_url: str = "http://gestor-ativos-brutos:8091"

    @property
    def gemini_configurado(self) -> bool:
        """Ha chave e ao menos um modelo; sem isso o Gemini e tratado como indisponivel."""
        return bool(self.gemini_api_key) and bool(self.gemini_modelos)

    @classmethod
    def do_ambiente(cls) -> Settings:
        raiz = Path(__file__).resolve().parents[1]
        modelos = _lista(os.getenv("GEMINI_MODELOS", MODELOS_GEMINI_PADRAO))
        reserva = LimiteDeModelo(rpm=_inteiro("GEMINI_RPM", "5", 1), rpd=_inteiro("GEMINI_RPD", "20", 1))
        cotas = (_inteiro("COTA_CHAT_PCT", "40"), _inteiro("COTA_CARD_PCT", "20"), _inteiro("COTA_LOTE_PCT", "40"))
        if sum(cotas) != 100:
            raise ConfiguracaoInvalida(f"COTA_CHAT_PCT + COTA_CARD_PCT + COTA_LOTE_PCT deve somar 100, soma {sum(cotas)}")
        return cls(
            ollama_url=os.getenv("OLLAMA_URL", "http://ollama:11434").rstrip("/"),
            modelo_chat=os.getenv("MODELO_CHAT", "qwen2.5:0.5b-instruct"),
            modelo_embed=os.getenv("MODELO_EMBED", "nomic-embed-text"),
            vetores_url=os.getenv("VETORES_URL") or None,
            rag_indice=Path(os.getenv("RAG_INDICE", str(raiz / "var" / "rag.sqlite"))),
            dir_skills=Path(os.getenv("DIR_SKILLS", str(raiz / "skills"))),
            dir_conhecimento=Path(os.getenv("DIR_CONHECIMENTO", str(raiz / "conhecimento"))),
            timeout_modelo_s=int(os.getenv("TIMEOUT_MODELO_S", "180")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
            gemini_modelos=modelos,
            gemini_limites=_limites(os.getenv("GEMINI_LIMITES", LIMITES_GEMINI_PADRAO), len(modelos), reserva),
            gemini_timeout_s=_inteiro("GEMINI_TIMEOUT_S", "30", 1),
            provedores_lote=_provedores("PROVEDORES_LOTE", "gemini,ollama"),
            provedores_chat=_provedores("PROVEDORES_CHAT", "gemini"),
            cota_chat_pct=cotas[0],
            cota_card_pct=cotas[1],
            cota_lote_pct=cotas[2],
            chat_max_dia_sessao=_inteiro("CHAT_MAX_DIA_SESSAO", "60", 1),
            chat_intervalo_s=_inteiro("CHAT_INTERVALO_S", "3"),
            gestor_url=os.getenv("GESTOR_URL", "http://gestor-ativos-brutos:8091").rstrip("/"),
        )
