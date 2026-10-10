"""Indexador incremental (TASK-IA-10): so trechos com hash novo sao
(re)gravados e vetorizados; trecho que sumiu das fichas sai do indice.

    python -m app.rag.indexador   # usa DIR_CONHECIMENTO e RAG_INDICE (indice textual)
"""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from app.rag import indice, trechos

LOTE_EMBED = 32
log = logging.getLogger("rag")


@dataclass
class ResumoIndexacao:
    novos: int = 0
    removidos: int = 0
    inalterados: int = 0
    com_vetor: bool = False
    total: int = 0


def indexar(dir_conhecimento: Path, caminho_indice: Path | None = None, embedder=None) -> ResumoIndexacao:
    todos = trechos.do_diretorio(Path(dir_conhecimento))
    conexao = indice.abrir(caminho_indice)
    resumo = ResumoIndexacao(com_vetor=embedder is not None, total=len(todos))
    try:
        atuais = {tid: (h, v is not None) for tid, h, v in conexao.execute(
            "SELECT trecho_id, hash, vetor FROM trecho")}
        linha_modelo = conexao.execute("SELECT valor FROM meta WHERE chave = 'modelo_embed'").fetchone()
        modelo_anterior = linha_modelo[0] if linha_modelo else None
        modelo_atual = getattr(embedder, "modelo", None)
        trocou_modelo = embedder is not None and modelo_anterior != modelo_atual

        pendentes = []
        for t in todos:
            gravado = atuais.get(t.trecho_id)
            sem_vetor = embedder is not None and gravado is not None and not gravado[1]
            if gravado is None or gravado[0] != t.hash() or sem_vetor or trocou_modelo:
                pendentes.append(t)
            else:
                resumo.inalterados += 1

        vetores: dict[str, bytes] = {}
        if embedder is not None:
            for i in range(0, len(pendentes), LOTE_EMBED):
                lote = pendentes[i:i + LOTE_EMBED]
                for t, v in zip(lote, embedder.vetores([t.texto for t in lote])):
                    vetores[t.trecho_id] = indice.para_blob(v)

        vigentes = {t.trecho_id for t in todos}
        sumiram = [tid for tid in atuais if tid not in vigentes]
        with conexao:
            for t in pendentes:
                conexao.execute(
                    "INSERT OR REPLACE INTO trecho (trecho_id, hash, texto, fonte, tipo, simbolo, setor, "
                    "disponivel_ate, vetor) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (t.trecho_id, t.hash(), t.texto, t.fonte, t.tipo, t.simbolo, t.setor,
                     t.disponivel_ate.isoformat(), vetores.get(t.trecho_id)))
                conexao.execute("DELETE FROM trecho_fts WHERE trecho_id = ?", (t.trecho_id,))
                conexao.execute("INSERT INTO trecho_fts (trecho_id, texto) VALUES (?, ?)", (t.trecho_id, t.texto))
            for tid in sumiram:
                conexao.execute("DELETE FROM trecho WHERE trecho_id = ?", (tid,))
                conexao.execute("DELETE FROM trecho_fts WHERE trecho_id = ?", (tid,))
            if embedder is not None:
                conexao.execute("INSERT OR REPLACE INTO meta (chave, valor) VALUES ('modelo_embed', ?)",
                                (modelo_atual,))
        resumo.novos = len(pendentes)
        resumo.removidos = len(sumiram)
    finally:
        conexao.close()
    return resumo


def main() -> int:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s rag - %(message)s")
    raiz = Path(__file__).resolve().parents[2]
    dir_conhecimento = Path(os.getenv("DIR_CONHECIMENTO", str(raiz / "conhecimento")))
    r = indexar(dir_conhecimento, indice.caminho_padrao(), None)
    log.info("Indexacao concluida | trechos=%s | novos=%s | removidos=%s | inalterados=%s | vetor=%s",
             r.total, r.novos, r.removidos, r.inalterados, r.com_vetor)
    return 0


if __name__ == "__main__":
    sys.exit(main())
