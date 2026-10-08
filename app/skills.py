"""Carga, selecao e hash das skills (`skills/<nome>/SKILL.md`). O conjunto ativo gera `skills@<hash>`.

Cada skill tem um cabecalho `chave: valor` entre `---` (nome, versao e, conforme o caso, `sempre`,
`horizonte`, `evidencias` ou `prefixo_evidencia`) e um corpo em Markdown que vira parte do prompt de
sistema. O hash cobre o nome e o conteudo de todos os arquivos de cada skill, em ordem estavel:
mudou uma virgula, mudou a versao. `versao_prompt` em opiniao_ia e VARCHAR(20): 'skills@' + 12 hex cabe.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Skill:
    nome: str
    versao: str
    hash: str
    meta: dict[str, str] = field(default_factory=dict, compare=False)
    corpo: str = field(default="", compare=False)


def _separar(texto: str) -> tuple[dict[str, str], str]:
    """(cabecalho, corpo). Sem cabecalho valido, tudo e corpo."""
    linhas = texto.replace("\r\n", "\n").split("\n")
    if not linhas or linhas[0].strip() != "---":
        return {}, texto.strip()
    try:
        fim = linhas.index("---", 1)
    except ValueError:
        return {}, texto.strip()
    meta: dict[str, str] = {}
    for linha in linhas[1:fim]:
        chave, _, valor = linha.partition(":")
        if chave.strip():
            meta[chave.strip()] = valor.strip()
    return meta, "\n".join(linhas[fim + 1:]).strip()


def listar(dir_skills: Path) -> list[Skill]:
    if not dir_skills.is_dir():
        return []
    saida: list[Skill] = []
    pastas = sorted(p for p in dir_skills.iterdir() if p.is_dir() and (p / "SKILL.md").is_file())
    for pasta in pastas:
        meta, corpo = _separar((pasta / "SKILL.md").read_text(encoding="utf-8"))
        saida.append(Skill(pasta.name, meta.get("versao", "0"), _hash_da_pasta(pasta)[:12], meta, corpo))
    return saida


def _hash_da_pasta(pasta: Path) -> str:
    h = hashlib.sha256()
    for arquivo in sorted(p for p in pasta.rglob("*") if p.is_file()):
        h.update(arquivo.relative_to(pasta).as_posix().encode())
        h.update(arquivo.read_bytes())
    return h.hexdigest()


def versao_do_conjunto(skills: list[Skill]) -> str:
    """`skills@<12 hex>`; conjunto vazio tem versao propria e estavel."""
    h = hashlib.sha256("|".join(f"{s.nome}:{s.versao}:{s.hash}" for s in skills).encode())
    return f"skills@{h.hexdigest()[:12]}"


def _lista(valor: str | None) -> set[str]:
    return {i.strip() for i in (valor or "").split(",") if i.strip()}


def selecionar(skills: list[Skill], horizonte: int, ids_evidencias: list[str]) -> list[Skill]:
    """So o que ajuda neste pedido: as skills `sempre`, a do horizonte e as de leitura das evidencias
    presentes (por id exato ou por prefixo). Menos contexto = resposta mais rapida e menos divagacao."""
    ids = set(ids_evidencias)
    escolhidas: list[Skill] = []
    for s in skills:
        sempre = s.meta.get("sempre", "").lower() == "true"
        do_horizonte = s.meta.get("horizonte") == str(horizonte)
        por_id = bool(_lista(s.meta.get("evidencias")) & ids)
        prefixo = s.meta.get("prefixo_evidencia")
        por_prefixo = bool(prefixo) and any(i.startswith(prefixo) for i in ids)
        if sempre or do_horizonte or por_id or por_prefixo:
            escolhidas.append(s)
    # ordem estavel: sempre primeiro, depois horizonte, depois leituras
    peso = lambda s: (0 if s.meta.get("sempre", "").lower() == "true" else 1 if s.meta.get("horizonte") else 2, s.nome)  # noqa: E731
    return sorted(escolhidas, key=peso)


def montar_sistema(escolhidas: list[Skill]) -> str:
    return "\n\n".join(f"[{s.nome}]\n{s.corpo}" for s in escolhidas if s.corpo)


def schema_da_resposta(dir_skills: Path) -> dict | None:
    """Schema de saida em skills/formato-resposta/schema.json, ou None se nao houver."""
    caminho = dir_skills / "formato-resposta" / "schema.json"
    if not caminho.is_file():
        return None
    return json.loads(caminho.read_text(encoding="utf-8"))
