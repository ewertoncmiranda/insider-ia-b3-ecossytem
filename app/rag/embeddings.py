"""Embeddings pelo Ollama (`/api/embed`, modelo MODELO_EMBED). Opcional: sem o
modelo baixado, `criar()` devolve None e o RAG funciona so com busca textual."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request

log = logging.getLogger("rag")


class EmbedderOllama:
    def __init__(self, url: str, modelo: str, timeout: int = 120):
        self.url = url.rstrip("/")
        self.modelo = modelo
        self.timeout = timeout

    def disponivel(self) -> bool:
        try:
            with urllib.request.urlopen(f"{self.url}/api/tags", timeout=5) as resposta:
                nomes = {m.get("name", "") for m in json.load(resposta).get("models", [])}
        except (urllib.error.URLError, OSError, ValueError):
            return False
        return any(n == self.modelo or n.startswith(self.modelo + ":") for n in nomes)

    def vetores(self, textos: list[str]) -> list[list[float]]:
        corpo = json.dumps({"model": self.modelo, "input": textos}).encode("utf-8")
        pedido = urllib.request.Request(f"{self.url}/api/embed", data=corpo,
                                        headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(pedido, timeout=self.timeout) as resposta:
            return json.load(resposta)["embeddings"]


def criar(url: str | None, modelo: str | None) -> EmbedderOllama | None:
    if not url or not modelo:
        return None
    embedder = EmbedderOllama(url, modelo)
    if not embedder.disponivel():
        log.warning("modelo de embeddings %s indisponivel em %s; RAG so textual", modelo, url)
        return None
    return embedder
