"""Fichas de **fundamentos** (TASK-IA-09): conceitos, formulas e estudos, a partir do painel.

Fonte = o conteudo estatico do `painel-ativos-frontend`, exportado em JSON por
`scripts/exportar_painel.mjs` (glossario basico e academico, padroes de velas, formulas por tema e
os cursos da trilha de estudos, cada curso ligado a um PDF com paginas por aula). Cada verbete,
formula ou aula vira uma secao `## ...`, e portanto um trecho citavel do RAG
(`fundamentos/<colecao>/<id>#<secao>`); o cabecalho guarda a origem no painel e, nos estudos, o PDF.

Dos PDFs entra so o que o painel ja escreveu sobre eles (objetivo, topicos, paginas), nunca o texto
do PDF: a ficha aponta onde ler, com pagina, sem copiar o material.

Conceito nao tem data: `disponivel_ate` fixo em 2000-01-01, para o trecho valer em qualquer pregao.

    python -m app.fichas.fundamentos --painel ../painel-ativos-frontend [--json arquivo] [--saida DIR]
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

from app.fichas.ficha import Ficha, gravar

DISPONIVEL_SEMPRE = "2000-01-01"
RAIZ_REPO = Path(__file__).resolve().parents[2]
_TAG = re.compile(r"<[^>]+>")
# rotulos de FormulasPage.js (CENARIOS)
CENARIOS = {"DAY_TRADE": "Day trade", "SWING": "Swing / reversão", "LONGO_PRAZO": "Longo prazo",
            "SETORIAL": "Comparação setorial", "MACRO": "Contexto macro"}

ORIGEM = {
    "glossario": "painel-ativos-frontend/public/js/pages/GlossarioPage.js",
    "academico": "painel-ativos-frontend/public/js/estudos/glossarioAcademico.js",
    "padroes": "painel-ativos-frontend/public/js/estudos/glossarioPadroes.js",
    "formulas": "painel-ativos-frontend/public/js/pages/FormulasPage.js",
    "estudos": "painel-ativos-frontend/public/js/estudos/cursos.js",
}


def _texto(valor) -> str:
    """Texto limpo: sem tags HTML e com espacos normalizados (listas viram itens separados por '; ')."""
    if valor is None:
        return ""
    if isinstance(valor, list):
        return "; ".join(t for t in (_texto(v) for v in valor) if t)
    return " ".join(_TAG.sub("", str(valor)).split())


def _linhas(*pares: tuple[str, object]) -> str:
    return "\n".join(f"- **{rotulo}:** {_texto(v)}" for rotulo, v in pares if _texto(v))


def _secoes_unicas(secoes: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Titulos repetidos ganham sufixo: o id do trecho e o titulo da secao."""
    vistos: dict[str, int] = {}
    saida = []
    for titulo, corpo in secoes:
        titulo = _texto(titulo) or "Sem título"
        n = vistos.get(titulo.lower(), 0) + 1
        vistos[titulo.lower()] = n
        saida.append((titulo if n == 1 else f"{titulo} ({n})", corpo))
    return saida


def _cabecalho(colecao: str, titulo: str, **extra) -> dict:
    return {"tipo": "fundamentos", "colecao": colecao, "titulo": _texto(titulo), **extra,
            "origem": ORIGEM[colecao], "disponivel_ate": DISPONIVEL_SEMPRE}


def _glossario(colecao: str, grupos: list[dict]) -> list[Ficha]:
    fichas = []
    for g in grupos:
        secoes = [("Resumo", _texto(g.get("resumo")) or _texto(g.get("titulo")))]
        for t in g.get("termos") or []:
            corpo = "\n\n".join(x for x in (
                _texto(t.get("definicao")),
                _linhas(("Sigla", t.get("sigla")), ("Exemplo", t.get("exemplo")), ("Cuidado", t.get("cuidado")),
                        ("Pergunta para estudo", t.get("pergunta")), ("Onde aparece no painel", t.get("onde")),
                        ("Referência", t.get("referencia")))) if x)
            secoes.append((t.get("termo"), corpo))
        fichas.append(Ficha(f"fundamentos/{colecao}/{g['id']}.md", _cabecalho(colecao, g.get("titulo")),
                            _secoes_unicas(secoes)))
    return fichas


def _padroes(padroes: list[dict]) -> list[Ficha]:
    secoes = [("Resumo", "Padrões de velas reconhecidos pelo detector da aba Velas: o que cada desenho sugere, "
                         "onde perde sentido e como o painel o detecta (regra mecânica, pode diferir do livro).")]
    for p in padroes:
        secoes.append((p.get("termo"), _linhas(
            ("Fundamento", p.get("fundamento")), ("Indica", p.get("indica")), ("Cenários", p.get("cenarios")),
            ("Combina com", p.get("combinaCom")), ("Neste painel", p.get("nestePainel")))))
    return [Ficha("fundamentos/padroes/velas.md", _cabecalho("padroes", "Padrões de velas"), _secoes_unicas(secoes))]


def _formulas(temas: list[dict]) -> list[Ficha]:
    fichas = []
    for tema in temas:
        secoes = [("Resumo", "\n\n".join(x for x in (_texto(tema.get("resumo")),
                                                     _linhas(("Fonte dos dados", tema.get("fonte")))) if x))]
        for item in tema.get("itens") or []:
            corpo = "\n\n".join(x for x in (
                _texto(item.get("descricao")),
                _linhas(("Fórmula", item.get("formula")), ("Situação", item.get("status")),
                        ("Contextos de uso", [CENARIOS.get(c, c) for c in item.get("cenarios") or []]))) if x)
            secoes.append((item.get("nome"), corpo))
        fichas.append(Ficha(f"fundamentos/formulas/{tema['id']}.md", _cabecalho("formulas", tema.get("titulo")),
                            _secoes_unicas(secoes)))
    return fichas


def _paginas(p) -> str:
    if isinstance(p, list) and len(p) == 2:
        return f"{p[0]}–{p[1]}" if p[0] != p[1] else str(p[0])
    return _texto(p)


def _estudos(cursos: list[dict]) -> list[Ficha]:
    fichas = []
    for c in cursos:
        pdf = _texto(c.get("pdf"))
        autoria = _texto(c.get("autoria") or c.get("instituicao") or c.get("origem"))
        secoes = [("Resumo", "\n\n".join(x for x in (
            _texto(c.get("descricao")),
            _linhas(("Autoria", autoria), ("Ano", c.get("ano")), ("Nível", c.get("nivel")),
                    ("Páginas", c.get("paginas")), ("Arquivo", f"painel-ativos-frontend/public/{pdf}" if pdf else ""),
                    ("Aviso", c.get("aviso")))) if x))]
        for m in c.get("modulos") or []:
            for a in m.get("aulas") or []:
                secoes.append((f"{_texto(m.get('titulo'))} — {_texto(a.get('titulo'))}", _linhas(
                    ("Páginas do PDF", _paginas(a.get("paginas"))), ("Objetivo", a.get("objetivo")),
                    ("Tópicos", a.get("topicos")), ("Atividade", a.get("atividade")))))
        cabecalho = _cabecalho("estudos", c.get("titulo"), pdf=f"painel-ativos-frontend/public/{pdf}" if pdf else "")
        fichas.append(Ficha(f"fundamentos/estudos/{c['id']}.md", cabecalho, _secoes_unicas(secoes)))
    return fichas


def montar_todas(dados: dict) -> list[Ficha]:
    """Puro: JSON exportado do painel -> fichas."""
    return (_glossario("glossario", dados.get("glossario") or [])
            + _glossario("academico", dados.get("academico") or [])
            + (_padroes(dados["padroes"]) if dados.get("padroes") else [])
            + _formulas(dados.get("formulas") or [])
            + _estudos(dados.get("cursos") or []))


def exportar_do_painel(painel: Path) -> dict:
    """Roda o exportador Node (so le o painel) e devolve o JSON."""
    script = RAIZ_REPO / "scripts" / "exportar_painel.mjs"
    resultado = subprocess.run(["node", str(script), str(painel)], capture_output=True, check=True,  # noqa: S603,S607
                               cwd=RAIZ_REPO, timeout=120)
    return json.loads(resultado.stdout.decode("utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.fichas.fundamentos", description=__doc__.splitlines()[0])
    parser.add_argument("--painel", type=Path, default=RAIZ_REPO.parent / "painel-ativos-frontend")
    parser.add_argument("--json", type=Path, help="JSON ja exportado (pula o Node)")
    parser.add_argument("--saida", type=Path,
                        default=Path(os.getenv("DIR_CONHECIMENTO", RAIZ_REPO / "conhecimento")))
    argumentos = parser.parse_args(argv)
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s fichas - %(message)s")
    log = logging.getLogger("fichas")

    dados = (json.loads(argumentos.json.read_text(encoding="utf-8")) if argumentos.json
             else exportar_do_painel(argumentos.painel))
    fichas = montar_todas(dados)
    hoje = date.today()
    gravadas = sum(gravar(f, argumentos.saida, hoje) for f in fichas)
    log.info("fundamentos: %s fichas, %s gravadas (hash novo), %s secoes", len(fichas), gravadas,
             sum(len(f.secoes) for f in fichas))
    return 0


if __name__ == "__main__":
    sys.exit(main())
