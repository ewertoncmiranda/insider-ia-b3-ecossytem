"""Ferramentas de leitura para o Gemini (function calling, TASK-IA-33, SPEC GEM-4).

Cinco funções só-leitura que fazem GETs no gestor:
  cotacao(s), fundamentos(s), opiniao(s), comunicados(s), comparar(s1, s2)

Contrato:
- Símbolo validado por `^[A-Z]{4}[0-9]{1,2}$` antes de qualquer chamada HTTP.
- Máximo 4 chamadas por mensagem (rejeitadas pela Cadeia); rastreado externamente.
- Resposta truncada a MAX_BYTES.
- Gestor fora do ar → devolver "dado indisponível" e continuar o chat.
- O modelo nunca monta URL nem SQL: qualquer argumento viaja como nome de ferramenta + params.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any

MAX_BYTES = 4096
MAX_CHAMADAS = 4
_SIMBOLO = re.compile(r"^[A-Z]{4}[0-9]{1,2}$")

# Rotas do gestor (NFR-IA-06: só GETs, sem efeito colateral)
_ROTAS: dict[str, str] = {
    "cotacao":      "/ativos/robusto/{s}",
    "fundamentos":  "/analises/{s}/fundamentos",
    "opiniao":      "/ativos/{s}/opiniao",
    "comunicados":  "/empresas/{s}/comunicados",
}

# Esquemas das ferramentas para o SDK do Gemini
FERRAMENTAS: list[dict] = [
    {
        "name": "cotacao",
        "description": "Retorna a cotação atual e variações do ativo no gestor.",
        "parameters": {
            "type": "OBJECT",
            "properties": {"s": {"type": "STRING", "description": "Ticker (ex: PETR4)"}},
            "required": ["s"],
        },
    },
    {
        "name": "fundamentos",
        "description": "Retorna fundamentos (P/L, ROE, dívida/EBITDA) do ativo.",
        "parameters": {
            "type": "OBJECT",
            "properties": {"s": {"type": "STRING", "description": "Ticker (ex: PETR4)"}},
            "required": ["s"],
        },
    },
    {
        "name": "opiniao",
        "description": "Retorna a opinião atual (por horizonte) gerada para o ativo.",
        "parameters": {
            "type": "OBJECT",
            "properties": {"s": {"type": "STRING", "description": "Ticker (ex: PETR4)"}},
            "required": ["s"],
        },
    },
    {
        "name": "comunicados",
        "description": "Retorna comunicados recentes da empresa.",
        "parameters": {
            "type": "OBJECT",
            "properties": {"s": {"type": "STRING", "description": "Ticker (ex: PETR4)"}},
            "required": ["s"],
        },
    },
    {
        "name": "comparar",
        "description": "Compara cotação e fundamentos de dois ativos.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "s1": {"type": "STRING", "description": "Primeiro ticker"},
                "s2": {"type": "STRING", "description": "Segundo ticker"},
            },
            "required": ["s1", "s2"],
        },
    },
]


class SimboloInvalido(ValueError):
    """Ticker não segue o padrão ^[A-Z]{4}[0-9]{1,2}$."""


class LimiteChamadasAtingido(RuntimeError):
    """Quinta chamada de ferramenta na mesma mensagem."""


def _validar(simbolo: Any) -> str:
    """Valida o símbolo antes de qualquer chamada HTTP; não normaliza maiúsculas/minúsculas."""
    s = str(simbolo or "").strip()
    if not _SIMBOLO.match(s):
        raise SimboloInvalido(f"símbolo inválido: {simbolo!r}")
    return s


def _get(url: str, timeout: int = 5) -> str:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:  # noqa: S310
            corpo = r.read()
    except (urllib.error.URLError, TimeoutError, OSError):
        return json.dumps({"erro": "dado indisponível"})
    if len(corpo) > MAX_BYTES:
        corpo = corpo[:MAX_BYTES]
    try:
        return corpo.decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        return json.dumps({"erro": "dado indisponível"})


def executar(nome: str, args: dict, gestor_url: str, contador: list[int]) -> str:
    """Executa uma ferramenta e devolve o resultado como string JSON (truncada a MAX_BYTES).

    `contador` é uma lista de um elemento [n] mutável; o chamador inicializa com [0] por mensagem.
    Lança `LimiteChamadasAtingido` na 5ª chamada.
    """
    contador[0] += 1
    if contador[0] > MAX_CHAMADAS:
        raise LimiteChamadasAtingido("máximo de 4 chamadas de ferramenta por mensagem atingido")

    gestor = gestor_url.rstrip("/")

    if nome == "comparar":
        s1 = _validar(args.get("s1"))
        s2 = _validar(args.get("s2"))
        dados1 = _get(f"{gestor}/ativos/robusto/{s1}")
        dados2 = _get(f"{gestor}/ativos/robusto/{s2}")
        resultado = {"s1": {"simbolo": s1, "dados": _parsear(dados1)},
                     "s2": {"simbolo": s2, "dados": _parsear(dados2)}}
        return _truncar(json.dumps(resultado, ensure_ascii=False))

    rota = _ROTAS.get(nome)
    if rota is None:
        return json.dumps({"erro": f"ferramenta desconhecida: {nome!r}"})

    s = _validar(args.get("s"))
    url = gestor + rota.replace("{s}", s)
    return _truncar(_get(url))


def _parsear(texto: str) -> Any:
    try:
        return json.loads(texto)
    except Exception:  # noqa: BLE001
        return texto


def _truncar(texto: str) -> str:
    if len(texto.encode("utf-8")) > MAX_BYTES:
        return texto.encode("utf-8")[:MAX_BYTES].decode("utf-8", errors="replace")
    return texto
