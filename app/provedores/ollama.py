"""Provedor Ollama: /api/chat com saida estruturada (`format` = JSON Schema) e temperatura 0 (NFR-IA-01).

`ProvedorLLM` e a porta: trocar de modelo e a variavel MODELO_CHAT; trocar de provedor e outra classe.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Protocol


class ErroDoProvedor(RuntimeError):
    pass


class ProvedorLLM(Protocol):
    nome: str

    def gerar(self, sistema: str, usuario: str, schema: dict) -> str: ...


class OllamaProvedor:
    def __init__(self, url: str, modelo: str, timeout_s: int = 180, semente: int = 7, num_ctx: int = 2048,
                 max_tokens: int = 700):
        self._url = url.rstrip("/")
        self.nome = modelo
        self._timeout = timeout_s
        self._opcoes = {"temperature": 0, "seed": semente, "num_ctx": num_ctx, "num_predict": max_tokens}

    def gerar(self, sistema: str, usuario: str, schema: dict) -> str:
        corpo = json.dumps({
            "model": self.nome,
            "stream": False,
            "format": schema,
            "options": self._opcoes,
            "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": usuario}],
        }).encode("utf-8")
        pedido = urllib.request.Request(f"{self._url}/api/chat", data=corpo,
                                        headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(pedido, timeout=self._timeout) as resposta:  # noqa: S310
                dados = json.loads(resposta.read())
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as erro:
            raise ErroDoProvedor(f"Ollama indisponível em {self._url}: {erro}") from erro
        return str((dados.get("message") or {}).get("content") or "")
