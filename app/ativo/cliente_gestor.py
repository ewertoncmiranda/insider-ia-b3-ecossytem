"""Cliente so leitura do gestor (SPEC 13.3, CTR-IA-03). O ia-opiniao nao acessa o MySQL (NFR-IA-06):
os dados do ativo vem dos GETs que o gestor ja oferece. Reutilizado pelas ferramentas do chat (IA-33).

`/ativos/robusto/{s}` fica de fora de proposito: ele pode consultar a BRAPI (gasta cota dela).
A cotacao sai de `/ativos/{s}/pregoes`, que le o COTAHIST oficial.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from typing import Any

SIMBOLO = re.compile(r"^[A-Z]{4}[0-9]{1,2}$")
GESTOR_URL_PADRAO = "http://gestor-ativos-brutos:8091"


class SimboloInvalido(ValueError):
    pass


class AtivoNaoEncontrado(LookupError):
    pass


class GestorIndisponivel(RuntimeError):
    pass


def validar_simbolo(simbolo: str) -> str:
    s = (simbolo or "").strip().upper()
    if not SIMBOLO.match(s):
        raise SimboloInvalido(f"símbolo inválido: {simbolo!r}")
    return s


class ClienteGestor:
    def __init__(self, url: str | None = None, timeout_s: int = 20):
        self._url = (url or os.getenv("GESTOR_URL", GESTOR_URL_PADRAO)).rstrip("/")
        self._timeout = timeout_s

    def _get(self, caminho: str, params: dict | None = None, opcional: bool = False) -> Any:
        url = f"{self._url}{caminho}" + (f"?{urllib.parse.urlencode(params)}" if params else "")
        try:
            with urllib.request.urlopen(url, timeout=self._timeout) as resposta:  # noqa: S310 - URL de config
                return json.loads(resposta.read().decode("utf-8"))
        except urllib.error.HTTPError as erro:
            if erro.code == 404:
                if opcional:
                    return None
                raise AtivoNaoEncontrado(caminho) from erro
            if opcional:
                return None
            raise GestorIndisponivel(f"gestor respondeu HTTP {erro.code} em {caminho}") from erro
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as erro:
            if opcional:
                return None
            raise GestorIndisponivel(f"gestor indisponível: {type(erro).__name__}") from erro

    def pregoes(self, simbolo: str, dias: int = 400) -> dict:
        """Velas diarias do ultimo ano e pouco (variacao de 12 meses precisa de ~252 pregoes)."""
        de = (date.today() - timedelta(days=dias)).isoformat()
        return self._get(f"/ativos/{validar_simbolo(simbolo)}/pregoes", {"intervalo": "dia", "de": de})

    def fundamentos(self, simbolo: str) -> dict | None:
        return self._get(f"/analises/{validar_simbolo(simbolo)}/fundamentos", opcional=True)

    def opiniao(self, simbolo: str) -> dict | None:
        return self._get(f"/ativos/{validar_simbolo(simbolo)}/opiniao", opcional=True)

    def comunicados(self, simbolo: str, quantidade: int = 3) -> dict | None:
        return self._get(f"/empresas/{validar_simbolo(simbolo)}/comunicados",
                         {"tamanho": quantidade, "pagina": 0}, opcional=True)
