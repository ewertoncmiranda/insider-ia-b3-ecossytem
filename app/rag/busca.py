"""Busca no indice com filtro de ponto no tempo (TASK-IA-10, SPEC 6.4/6.5).

Filtro duro, no SQL: `disponivel_ate do trecho <= disponivel_ate pedido` (a
data do pregao analisado) - o mesmo indice serve ao backtest sem vazamento.
Ranking: textual (FTS5, bm25) e, se houver vetores e embedder, por cosseno;
os dois combinados por fusao de rankings (RRF). Sem vetor, so textual.
"""

from __future__ import annotations

import math
import re
from datetime import date
from pathlib import Path

from app.rag import indice as indice_sqlite
from app.rag.trechos import Trecho

RRF_K = 60
CANDIDATOS = 200
_COLUNAS = ("trecho_id", "texto", "fonte", "tipo", "simbolo", "setor", "disponivel_ate")
_SELECT = ", ".join(f"t.{c}" for c in _COLUNAS)


def _filtro(disponivel_ate: date, simbolo, setor, tipo) -> tuple[str, list]:
    condicoes, parametros = ["t.disponivel_ate <= ?"], [disponivel_ate.isoformat()]
    for coluna, valor in (("simbolo", simbolo), ("setor", setor), ("tipo", tipo)):
        if valor is not None:
            condicoes.append(f"t.{coluna} = ?")
            parametros.append(valor)
    return " AND ".join(condicoes), parametros


def _trecho(linha, pontuacao: float) -> Trecho:
    tid, texto, fonte, tipo, simbolo, setor, disp = linha
    return Trecho(tid, texto, fonte, tipo, simbolo, setor, date.fromisoformat(disp), pontuacao)


def _consulta_fts(consulta: str) -> str | None:
    palavras = [p for p in re.findall(r"\w+", consulta.lower()) if len(p) >= 2]
    return " OR ".join(f'"{p}"' for p in palavras[:30]) or None


def _recencia(disponivel_ate: str) -> int:
    return -date.fromisoformat(disponivel_ate).toordinal()


def _cosseno(a: list[float], b: list[float]) -> float:
    num = sum(x * y for x, y in zip(a, b))
    den = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return num / den if den else 0.0


def buscar(consulta: str, *, disponivel_ate: date, simbolo: str | None = None, setor: str | None = None,
           tipo: str | None = None, k: int = 5, indice: Path | None = None, embedder=None) -> list[Trecho]:
    """Top-k trechos relevantes e ja publicos em `disponivel_ate`.

    `embedder` e opcional (qualquer objeto com `.vetores(textos)`): sem ele, busca so textual.
    Desde 2026-10-08 o servico nao tem embedder proprio (o Ollama saiu, DEC-IA-11)."""
    where, parametros = _filtro(disponivel_ate, simbolo, setor, tipo)
    conexao = indice_sqlite.abrir(indice)
    try:
        rankings: list[list[str]] = []
        linhas: dict[str, tuple] = {}

        fts = _consulta_fts(consulta)
        if fts:
            ranking = []
            for linha in conexao.execute(
                f"SELECT {_SELECT}, bm25(trecho_fts) AS nota FROM trecho_fts "
                f"JOIN trecho t ON t.trecho_id = trecho_fts.trecho_id "
                f"WHERE trecho_fts MATCH ? AND {where} ORDER BY nota LIMIT ?",
                [fts, *parametros, CANDIDATOS],
            ):
                linhas[linha[0]] = linha[:-1]
                ranking.append(linha[0])
            rankings.append(ranking)

        tem_vetor = conexao.execute(
            f"SELECT 1 FROM trecho t WHERE t.vetor IS NOT NULL AND {where} LIMIT 1", parametros).fetchone()
        if tem_vetor and embedder is not None:
            alvo = embedder.vetores([consulta])[0]
            notas = []
            for linha in conexao.execute(
                    f"SELECT {_SELECT}, t.vetor FROM trecho t WHERE t.vetor IS NOT NULL AND {where}", parametros):
                notas.append((_cosseno(alvo, indice_sqlite.de_blob(linha[-1])), linha[:-1]))
            notas.sort(key=lambda x: (-x[0], x[1][0]))
            for _, linha in notas[:CANDIDATOS]:
                linhas.setdefault(linha[0], linha)
            rankings.append([linha[0] for _, linha in notas[:CANDIDATOS]])
    finally:
        conexao.close()

    # Busca sobre um papel ou setor: entre as linhas dele, o ano mais recente ja
    # publico importa mais que a diferenca de bm25 entre linhas parecidas.
    if (simbolo or setor) and linhas:
        rankings.append(sorted(linhas, key=lambda tid: (_recencia(linhas[tid][6]), tid)))

    fusao: dict[str, float] = {}
    for ranking in rankings:
        for posicao, tid in enumerate(ranking):
            fusao[tid] = fusao.get(tid, 0.0) + 1.0 / (RRF_K + posicao + 1)
    # Empate de relevancia (linhas anuais da mesma ficha casam igual): vence a
    # mais recente ja publica - e a que interessa a quem analisa o pregao.
    melhores = sorted(fusao, key=lambda tid: (-fusao[tid], _recencia(linhas[tid][6]), tid))[:k]
    return [_trecho(linhas[tid], round(fusao[tid], 6)) for tid in melhores]


def por_metadado(*, disponivel_ate: date, simbolo: str | None = None, setor: str | None = None,
                 tipo: str | None = None, secoes: tuple[str, ...] = ("resumo",),
                 indice: Path | None = None) -> list[Trecho]:
    """Leitura direta sem vetor (SPEC 6.5 passo 1): as secoes pedidas das
    fichas que casam com os metadados, ja publicas em `disponivel_ate`."""
    where, parametros = _filtro(disponivel_ate, simbolo, setor, tipo)
    sufixos = " OR ".join("t.trecho_id LIKE ?" for _ in secoes)
    parametros += [f"%#{s}" for s in secoes]
    conexao = indice_sqlite.abrir(indice)
    try:
        linhas = conexao.execute(
            f"SELECT {_SELECT} FROM trecho t WHERE {where} AND ({sufixos}) ORDER BY t.tipo, t.trecho_id",
            parametros).fetchall()
    finally:
        conexao.close()
    return [_trecho(linha, 0.0) for linha in linhas]


__all__ = ["Trecho", "buscar", "por_metadado"]
