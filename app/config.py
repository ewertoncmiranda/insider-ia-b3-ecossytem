"""Configuracao: toda variavel de ambiente do servico passa por aqui (fonte unica)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


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

    @classmethod
    def do_ambiente(cls) -> Settings:
        raiz = Path(__file__).resolve().parents[1]
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
        )
