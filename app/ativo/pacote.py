"""Pacote do ativo (CTR-IA-03, TASK-IA-35): o que o card IA e o chat sabem de um ativo, sem cota.

Montado so com GETs do gestor + manchetes. Campo sem dado e `None` (nunca 0). Cache em memoria por
ativo: o pregao so muda uma vez por dia, entao 15 minutos bastam e poupam o gestor.
"""

from __future__ import annotations

import threading
import time
from decimal import Decimal
from typing import Callable

from app.ativo.cliente_gestor import AtivoNaoEncontrado, ClienteGestor, validar_simbolo
from app.ativo.noticias import buscar_manchetes

AVISO = "Leitura automática dos números, regra experimental. Não é recomendação de investimento."
VALIDADE_S = 15 * 60
MAX_SINAIS, MAX_COMUNICADOS, MAX_MANCHETES = 3, 3, 5
PREGOES_1M, PREGOES_12M = 21, 252

_cache: dict[str, tuple[float, dict]] = {}
_trava = threading.Lock()


def _num(valor) -> float | None:
    if valor is None:
        return None
    try:
        return float(Decimal(str(valor)))
    except (ArithmeticError, ValueError):
        return None


def _variacao(atual: float | None, antes: float | None) -> float | None:
    if atual is None or not antes:
        return None
    return round(atual / antes - 1, 4)


def cotacao(pregoes: dict | None) -> tuple[dict, str | None]:
    """Fechamento do ultimo pregao e variacoes em 1 pregao, ~1 mes (21) e ~12 meses (252)."""
    velas = [v for v in (pregoes or {}).get("velas") or [] if _num(v.get("fechamento")) is not None]
    if not velas:
        return {"fechamento": None, "variacao_1d": None, "variacao_1m": None, "variacao_12m": None}, None
    fech = [_num(v["fechamento"]) for v in velas]
    ultimo = fech[-1]

    def atras(n: int) -> float | None:
        return fech[-1 - n] if len(fech) > n else None

    return {"fechamento": ultimo, "variacao_1d": _variacao(ultimo, atras(1)),
            "variacao_1m": _variacao(ultimo, atras(PREGOES_1M)),
            "variacao_12m": _variacao(ultimo, atras(PREGOES_12M))}, velas[-1].get("data")


def fundamentos(dados: dict | None) -> dict:
    """Indicadores que o gestor ja calcula (insight do dia). ROE e divida nao vem desta rota: ficam fora."""
    detalhes = (dados or {}).get("detalhes") or {}
    snap, val = detalhes.get("snapshot_mercado") or {}, detalhes.get("valuation") or {}
    pl = _num(snap.get("preco_lucro"))
    return {
        "pl": round(pl, 2) if pl is not None else None,
        "lpa": _num(snap.get("lucro_por_acao")),
        "vpa": _num(val.get("vpa")),
        "earnings_yield_percent": _num(val.get("earnings_yield_percent") or detalhes.get("earnings_yield_percent")),
        "preco_justo_graham": _num((dados or {}).get("precoJustoGraham")),
        "margem_seguranca_percent": _num((dados or {}).get("margemSegurancaPercent")),
        "classificacao_pl": val.get("classificacao_pl"),
    }


def sinais_e_opiniao(dados: dict | None) -> tuple[list[dict], list[dict], str | None]:
    """3 evidencias mais fortes do horizonte mais curto e a opiniao gravada de cada horizonte."""
    horizontes = sorted((dados or {}).get("horizontes") or [], key=lambda h: h.get("horizontePregoes") or 0)
    opiniao = [{"horizonte_pregoes": h.get("horizontePregoes"), "opiniao": h.get("opiniao"),
                "risco": h.get("risco"), "origem": h.get("origem")} for h in horizontes]
    evidencias = (horizontes[0].get("evidencias") if horizontes else None) or []
    fortes = sorted(evidencias, key=lambda e: -abs(e.get("direcao") or 0))[:MAX_SINAIS]
    sinais = [{"id": e.get("id"), "rotulo": e.get("rotulo"), "valor": e.get("valor"), "direcao": e.get("direcao")}
              for e in fortes]
    return sinais, opiniao, (dados or {}).get("dataPregao")


def comunicados(dados: dict | None) -> list[dict]:
    return [{"data": c.get("dataEntrega") or c.get("dataReferencia"), "titulo": c.get("assunto") or c.get("tipo"),
             "categoria": c.get("categoriaRotulo"), "link": c.get("link")}
            for c in ((dados or {}).get("comunicados") or [])[:MAX_COMUNICADOS]]


def montar_pacote(simbolo: str, cliente: ClienteGestor | None = None,
                  manchetes: Callable[[str], list[dict]] = buscar_manchetes) -> dict:
    """Levanta SimboloInvalido, AtivoNaoEncontrado (sem pregao algum) ou GestorIndisponivel."""
    s = validar_simbolo(simbolo)
    cliente = cliente or ClienteGestor()
    cot, data_cotacao = cotacao(cliente.pregoes(s))
    sinais, opiniao, data_opiniao = sinais_e_opiniao(cliente.opiniao(s))
    if data_cotacao is None and not opiniao:
        raise AtivoNaoEncontrado(s)
    return {
        "simbolo": s,
        "data_pregao": data_cotacao or data_opiniao,
        "cotacao": cot,
        "fundamentos": fundamentos(cliente.fundamentos(s)),
        "sinais": sinais,
        "opiniao": opiniao,
        "comunicados": comunicados(cliente.comunicados(s, MAX_COMUNICADOS)),
        "manchetes": manchetes(s)[:MAX_MANCHETES],
        "aviso": AVISO,
    }


def pacote(simbolo: str, cliente: ClienteGestor | None = None, agora: Callable[[], float] = time.monotonic) -> dict:
    """`montar_pacote` com cache de 15 minutos por ativo."""
    s = validar_simbolo(simbolo)
    with _trava:
        guardado = _cache.get(s)
        if guardado and agora() - guardado[0] < VALIDADE_S:
            return guardado[1]
    dados = montar_pacote(s, cliente)
    with _trava:
        _cache[s] = (agora(), dados)
    return dados
