"""Guardas do chat (TASK-IA-34, SPEC GEM-4).

- Limites por sessão: CHAT_MAX_DIA_SESSAO mensagens e CHAT_INTERVALO_S entre elas.
- Classificador de tema: lista de palavras + RAG; perguntas fora de mercado/finanças/B3
  retornam `CodigoErro.FORA_DO_TEMA`.
- Número sem fonte no texto da resposta → evento `aviso`.
- Vocabulário proibido → uma regeneração (sinalizado, a decisão fica no api.py).
- Relógio injetável para os testes.

Nenhuma guarda levanta exceção sem causa; todas devolvem tipos simples.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import datetime, timezone
from enum import Enum
from typing import Any

Relogio = Callable[[], datetime]


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


class CodigoErro(str, Enum):
    INDISPONIVEL = "INDISPONIVEL"
    LIMITE = "LIMITE"
    FORA_DO_TEMA = "FORA_DO_TEMA"
    ENTRADA_INVALIDA = "ENTRADA_INVALIDA"


class LimiteAtingido(RuntimeError):
    def __init__(self, codigo: CodigoErro, mensagem: str, tentar_apos: str | None = None):
        super().__init__(mensagem)
        self.codigo = codigo
        self.tentar_apos = tentar_apos


# ---------------------------------------------------------------------------
# Limites de sessão
# ---------------------------------------------------------------------------

def verificar_limites(sessao_id: str, sessoes: Any, max_dia: int,
                      intervalo_s: int, agora: Relogio = _agora_utc) -> None:
    """Levanta LimiteAtingido se a sessão estiver fora do limite diário ou muito frequente."""
    ts = agora().timestamp()
    total_hoje = sessoes.total_hoje(sessao_id)
    if total_hoje >= max_dia:
        raise LimiteAtingido(CodigoErro.LIMITE,
                             f"Limite diário de {max_dia} mensagens por sessão atingido.")
    ultima = sessoes.ultima_mensagem_usuario(sessao_id)
    if ultima is not None and ts - ultima < intervalo_s:
        raise LimiteAtingido(CodigoErro.LIMITE,
                             f"Aguarde {intervalo_s} s entre mensagens.")


# ---------------------------------------------------------------------------
# Classificador de tema (palavras-chave, sem ML)
# ---------------------------------------------------------------------------

# Termos que indicam contexto de mercado financeiro/B3
_TERMOS_FINANCEIROS = re.compile(
    r"\b(ação|ações|ativo|ativos|bolsa|b3|mercado|cotação|preço|pregão"
    r"|ticker|símbolo|dividendo|dividendos|resultado|balanço|lucro"
    r"|risco|volatilidade|momentum|fundamento|fundamentos|valuation"
    r"|roi|roe|ebitda|p/l|pl|pvp|dy|cdi|selic|ibovespa|ibov"
    r"|fii|bdr|etf|debênture|opção|investir|carteira"
    r"|patrimônio|rendimento|retorno|inflação|ipca|câmbio|dólar|euro"
    r"|spread|yield|cupom|emissão|comunicado|fato relevante)\b",
    re.IGNORECASE,
)

# Termos que, sem qualquer indicador financeiro, sinalizam fora do tema
_TERMOS_NAO_FINANCEIROS = re.compile(
    r"\b(receita de|ingredientes|cozinha|culinária|preparo|temperatura de forno"
    r"|esporte|futebol|basquete|política|partido|eleição|votação"
    r"|novela|série|filme|música|letra de|horóscopo|astrologia"
    r"|academia|exercício|dieta|nutrição|saúde)\b",
    re.IGNORECASE,
)

# Padrão de ticker (4 letras + 1-2 dígitos)
_TICKER = re.compile(r"\b[A-Z]{4}[0-9]{1,2}\b")


def classificar_tema(mensagem: str) -> CodigoErro | None:
    """Devolve FORA_DO_TEMA se a mensagem for claramente fora de mercado, ou None se OK."""
    tem_ticker = bool(_TICKER.search(mensagem))
    tem_financeiro = bool(_TERMOS_FINANCEIROS.search(mensagem))
    tem_nao_fin = bool(_TERMOS_NAO_FINANCEIROS.search(mensagem))

    if tem_ticker or tem_financeiro:
        return None
    if tem_nao_fin:
        return CodigoErro.FORA_DO_TEMA
    # Mensagem curta sem nenhuma pista → aceitar; o sistema prompt lida
    if len(mensagem.split()) <= 6:
        return None
    # Mensagem longa sem termo financeiro
    return CodigoErro.FORA_DO_TEMA


# ---------------------------------------------------------------------------
# Número sem fonte
# ---------------------------------------------------------------------------

_NUMERO_PERCENTUAL = re.compile(r"\b\d{1,3}(?:[.,]\d{1,2})?[%\s]*(?:ao\s+ano|a\.?a\.?|ao\s+mês|a\.?m\.?)?\b")
_FONTE = re.compile(r"\(fonte:|segundo|de acordo|conforme|dados de|cotação de|\[trecho_id|rag:", re.IGNORECASE)


def detectar_numeros_sem_fonte(texto: str) -> list[str]:
    """Devolve lista de números suspeitos (percentuais/monetários sem indicação de fonte)."""
    if _FONTE.search(texto):
        return []
    numeros = _NUMERO_PERCENTUAL.findall(texto)
    return [n.strip() for n in numeros[:3]]


# ---------------------------------------------------------------------------
# Vocabulário proibido (uma regeneração)
# ---------------------------------------------------------------------------

_VOCAB_PROIBIDO = re.compile(
    r"\b(garanto|garantido|certeza|com certeza|vai subir|vai cair"
    r"|invista|recomendo|compre|venda agora|oportunidade imperdível)\b",
    re.IGNORECASE,
)


def contem_vocab_proibido(texto: str) -> bool:
    """Verdadeiro se o texto contiver promessas ou recomendações diretas."""
    return bool(_VOCAB_PROIBIDO.search(texto))
