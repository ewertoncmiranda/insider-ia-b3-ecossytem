"""Indice SQLite do RAG (DEC-IA-02: SQLite primeiro). Tabela de trechos com o
vetor em BLOB (float32) e FTS5 para a busca textual. Derivado das fichas:
apagar o arquivo e reindexar reconstroi tudo."""

from __future__ import annotations

import os
import sqlite3
import struct
from pathlib import Path

ESQUEMA = """
CREATE TABLE IF NOT EXISTS trecho (
    trecho_id      TEXT PRIMARY KEY,
    hash           TEXT NOT NULL,
    texto          TEXT NOT NULL,
    fonte          TEXT NOT NULL,
    tipo           TEXT NOT NULL,
    simbolo        TEXT,
    setor          TEXT,
    disponivel_ate TEXT NOT NULL,
    vetor          BLOB
);
CREATE INDEX IF NOT EXISTS idx_trecho_filtro ON trecho (tipo, simbolo, disponivel_ate);
CREATE VIRTUAL TABLE IF NOT EXISTS trecho_fts USING fts5(
    trecho_id UNINDEXED, texto, tokenize = 'unicode61 remove_diacritics 2'
);
CREATE TABLE IF NOT EXISTS meta (chave TEXT PRIMARY KEY, valor TEXT);
"""


def caminho_padrao() -> Path:
    raiz = Path(__file__).resolve().parents[2]
    return Path(os.getenv("RAG_INDICE", str(raiz / "var" / "rag.sqlite")))


def abrir(caminho: Path | None = None) -> sqlite3.Connection:
    caminho = Path(caminho) if caminho else caminho_padrao()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(str(caminho))
    conexao.executescript(ESQUEMA)
    return conexao


def para_blob(vetor: list[float]) -> bytes:
    return struct.pack(f"{len(vetor)}f", *vetor)


def de_blob(blob: bytes) -> list[float]:
    return list(struct.unpack(f"{len(blob) // 4}f", blob))
