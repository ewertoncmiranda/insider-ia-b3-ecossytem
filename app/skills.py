"""Carga e hash das skills (`skills/<nome>/SKILL.md`). O conjunto ativo gera `skills@<hash>`.

O hash cobre o nome e o conteudo de todos os arquivos de cada skill, em ordem estavel: mudou uma
virgula, mudou a versao. `versao_prompt` em opiniao_ia e VARCHAR(20): 'skills@' + 12 hex cabe.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

_VERSAO = re.compile(r"^versao:\s*(\S+)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class Skill:
    nome: str
    versao: str
    hash: str


def listar(dir_skills: Path) -> list[Skill]:
    if not dir_skills.is_dir():
        return []
    saida: list[Skill] = []
    pastas = sorted(p for p in dir_skills.iterdir() if p.is_dir() and (p / "SKILL.md").is_file())
    for pasta in pastas:
        texto = (pasta / "SKILL.md").read_text(encoding="utf-8")
        achou = _VERSAO.search(texto)
        saida.append(Skill(pasta.name, achou.group(1) if achou else "0", _hash_da_pasta(pasta)[:12]))
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
