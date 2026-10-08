"""Provedor Gemini (TASK-IA-24, DEC-IA-06/09/10) pelo SDK `google-genai`.

- `gerar(sistema, usuario, schema) -> str`: JSON pedido por schema (`response_json_schema`), temperatura 0.
- `conversar(mensagens, sistema) -> Iterator[str]`: streaming de texto puro para o chat (CTR-IA-02).
  `mensagens` = [{"papel": "usuario" | "modelo", "texto": "..."}], da mais antiga para a mais nova.
- 429 vira `ErroDeCota(espera_s, diaria)`; 5xx, timeout e rede viram `ErroDoProvedor`.
  Sem segunda tentativa aqui: quem decide o proximo passo e a cadeia (TASK-IA-26) com o governador.

A chave nunca entra em mensagem de erro, repr ou log: toda mensagem passa por `_limpar`.
"""

from __future__ import annotations

import re
from collections.abc import Iterator, Sequence
from typing import Any

from app.provedores.base import ErroDoProvedor

try:  # vem com o google-genai; sem ele o modulo ainda importa (testes com cliente falso)
    import httpx

    _ERROS_DE_REDE: tuple[type[BaseException], ...] = (httpx.TransportError, TimeoutError, OSError)
except ImportError:  # pragma: no cover
    _ERROS_DE_REDE = (TimeoutError, OSError)

PAPEIS = {"usuario": "user", "modelo": "model"}
_PADRAO_CHAVE = re.compile(r"AIza[0-9A-Za-z_\-]{20,}")
_PADRAO_PARAM = re.compile(r"(key=)[^&\s\"']+", re.IGNORECASE)
_PADRAO_ATRASO = re.compile(r"^\s*(\d+(?:\.\d+)?)s\s*$")


class ErroDeCota(ErroDoProvedor):
    """429 do Gemini. `espera_s` vem do `retryDelay` (None se ausente); `diaria` = cota do dia acabou."""

    def __init__(self, mensagem: str, espera_s: float | None = None, diaria: bool = False):
        super().__init__(mensagem)
        self.espera_s = espera_s
        self.diaria = diaria


def _limpar(texto: str, chave: str) -> str:
    if chave:
        texto = texto.replace(chave, "***")
    texto = _PADRAO_CHAVE.sub("***", texto)
    return _PADRAO_PARAM.sub(r"\1***", texto)[:300]


def _detalhes_429(corpo: Any) -> tuple[float | None, bool]:
    """Le `RetryInfo.retryDelay` ("17s") e se alguma violacao e de cota diaria (`...PerDay...`)."""
    erro = corpo.get("error", corpo) if isinstance(corpo, dict) else {}
    espera: float | None = None
    diaria = False
    for item in erro.get("details") or []:
        if not isinstance(item, dict):
            continue
        atraso = _PADRAO_ATRASO.match(str(item.get("retryDelay") or ""))
        if atraso:
            espera = float(atraso.group(1))
        for violacao in item.get("violations") or []:
            ids = f"{violacao.get('quotaId', '')} {violacao.get('quotaMetric', '')}"
            if "perday" in ids.lower().replace("_", ""):
                diaria = True
    mensagem = str(erro.get("message") or "").lower()
    if "per day" in mensagem or "daily" in mensagem:
        diaria = True
    return espera, diaria


class GeminiProvedor:
    """Um modelo Gemini. `cliente` e um `google.genai.Client` (ou dublê com `.models`)."""

    def __init__(self, cliente: Any, modelo: str, chave: str = "", temperatura_chat: float = 0.2):
        self.nome = modelo
        self._cliente = cliente
        self._chave = chave
        self._temperatura_chat = temperatura_chat

    def __repr__(self) -> str:
        return f"GeminiProvedor(modelo={self.nome!r})"

    def _traduzir(self, erro: BaseException) -> ErroDoProvedor:
        codigo = getattr(erro, "code", None)
        if isinstance(codigo, int):
            mensagem = _limpar(str(getattr(erro, "message", "") or ""), self._chave)
            if codigo == 429:
                espera, diaria = _detalhes_429(getattr(erro, "details", None))
                return ErroDeCota(f"Gemini {self.nome}: cota esgotada (429). {mensagem}".strip(), espera, diaria)
            return ErroDoProvedor(f"Gemini {self.nome}: HTTP {codigo}. {mensagem}".strip())
        if isinstance(erro, _ERROS_DE_REDE):
            tipo = "tempo esgotado" if "timeout" in type(erro).__name__.lower() else "falha de rede"
            return ErroDoProvedor(f"Gemini {self.nome}: {tipo} ({type(erro).__name__})")
        return ErroDoProvedor(f"Gemini {self.nome}: {type(erro).__name__}: {_limpar(str(erro), self._chave)}")

    def gerar(self, sistema: str, usuario: str, schema: dict) -> str:
        config = {"system_instruction": sistema, "temperature": 0,
                  "response_mime_type": "application/json", "response_json_schema": schema}
        try:
            resposta = self._cliente.models.generate_content(model=self.nome, contents=usuario, config=config)
        except ErroDoProvedor:
            raise
        except Exception as erro:  # noqa: BLE001 - qualquer falha do SDK vira erro do provedor
            raise self._traduzir(erro) from None
        texto = getattr(resposta, "text", None)
        if not texto:
            raise ErroDoProvedor(f"Gemini {self.nome}: resposta vazia")
        return str(texto)

    def conversar(self, mensagens: Sequence[dict], sistema: str) -> Iterator[str]:
        conteudos = []
        for m in mensagens:
            papel = PAPEIS.get(str(m.get("papel")))
            if papel is None:
                raise ValueError(f"papel desconhecido: {m.get('papel')!r}")
            conteudos.append({"role": papel, "parts": [{"text": str(m.get("texto") or "")}]})
        config = {"system_instruction": sistema, "temperature": self._temperatura_chat}
        try:
            for pedaco in self._cliente.models.generate_content_stream(
                    model=self.nome, contents=conteudos, config=config):
                texto = getattr(pedaco, "text", None)
                if texto:
                    yield str(texto)
        except ErroDoProvedor:
            raise
        except Exception as erro:  # noqa: BLE001
            raise self._traduzir(erro) from None


def criar_cliente(chave: str, timeout_s: int = 30) -> Any:
    """Cliente real do SDK: timeout por chamada e nenhuma nova tentativa automatica."""
    from google import genai
    from google.genai import types

    return genai.Client(api_key=chave, http_options=types.HttpOptions(
        timeout=int(timeout_s * 1000), retry_options=types.HttpRetryOptions(attempts=1)))


def criar_provedores(chave: str, modelos: Sequence[str], timeout_s: int = 30,
                     cliente: Any | None = None) -> list[GeminiProvedor]:
    """Um provedor por modelo, na ordem de GEMINI_MODELOS. Sem chave: lista vazia (Gemini indisponivel)."""
    if not chave or not modelos:
        return []
    cliente = cliente if cliente is not None else criar_cliente(chave, timeout_s)
    return [GeminiProvedor(cliente, m, chave=chave) for m in modelos]
