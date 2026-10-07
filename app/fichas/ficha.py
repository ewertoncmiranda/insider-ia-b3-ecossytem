"""Ficha .md com cabecalho YAML (SPEC 6.3): montagem, hash estavel e gravacao.

O hash cobre o cabecalho (sem `gerado_em` e `hash`) e o corpo: rodar de novo
com os mesmos dados produz o mesmo hash, e o arquivo nao e regravado - nem a
data de geracao muda. Puro, exceto `gravar`.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

LIMITE_ATIVO_BYTES = 4096
CAMPOS_FORA_DO_HASH = ("gerado_em", "hash")


@dataclass
class Ficha:
    caminho: str                      # relativo a conhecimento/, ex.: "ativos/PETR4.md"
    cabecalho: dict                   # ordem preservada na saida
    secoes: list[tuple[str, str]] = field(default_factory=list)  # (titulo, corpo)

    def corpo(self) -> str:
        return "".join(f"## {titulo}\n\n{texto.strip()}\n\n" for titulo, texto in self.secoes).rstrip() + "\n"

    def hash(self) -> str:
        base = _yaml({k: v for k, v in self.cabecalho.items() if k not in CAMPOS_FORA_DO_HASH}) + self.corpo()
        return hashlib.sha256(base.encode("utf-8")).hexdigest()

    def texto(self, gerado_em: date) -> str:
        cabecalho = {**self.cabecalho, "gerado_em": gerado_em.isoformat(), "hash": self.hash()}
        return f"---\n{_yaml(cabecalho)}---\n\n{self.corpo()}"


def _yaml(dados: dict) -> str:
    """YAML minimo e deterministico (escalares e listas de escalares)."""
    linhas = []
    for chave, valor in dados.items():
        if isinstance(valor, (list, tuple)):
            linhas.append(f"{chave}: [{', '.join(_escalar(v) for v in valor)}]")
        else:
            linhas.append(f"{chave}: {_escalar(valor)}")
    return "\n".join(linhas) + "\n"


def _escalar(valor) -> str:
    if valor is None:
        return "null"
    if isinstance(valor, bool):
        return "true" if valor else "false"
    if isinstance(valor, (int, float)):
        return str(valor)
    if isinstance(valor, date):
        return valor.isoformat()
    texto = str(valor)
    if any(c in texto for c in ":#[]{},&*!|>'\"%@`") or texto != texto.strip():
        return '"' + texto.replace('\\', '\\\\').replace('"', '\\"') + '"'
    return texto


def hash_gravado(arquivo: Path) -> str | None:
    """O `hash:` do cabecalho de uma ficha ja gravada, ou None."""
    if not arquivo.exists():
        return None
    for linha in arquivo.read_text(encoding="utf-8").splitlines()[1:40]:
        if linha == "---":
            break
        if linha.startswith("hash: "):
            return linha[6:].strip()
    return None


def gravar(ficha: Ficha, raiz: Path, hoje: date) -> bool:
    """Grava se o hash mudou; devolve True quando gravou."""
    destino = raiz / ficha.caminho
    if hash_gravado(destino) == ficha.hash():
        return False
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(ficha.texto(hoje), encoding="utf-8", newline="\n")
    return True


# --- formatacao (pt-BR, deterministica) ------------------------------------

def pct(valor: float | None, casas: int = 1) -> str:
    if valor is None:
        return "—"
    return f"{valor * 100:+.{casas}f}%".replace(".", ",")


def pct_sem_sinal(valor: float | None, casas: int = 1) -> str:
    if valor is None:
        return "—"
    return f"{valor * 100:.{casas}f}%".replace(".", ",")


def num(valor: float | None, casas: int = 1) -> str:
    if valor is None:
        return "—"
    return f"{valor:.{casas}f}".replace(".", ",")


def tabela(cabecalho: list[str], linhas: list[list[str]]) -> str:
    saida = ["| " + " | ".join(cabecalho) + " |", "|" + "|".join("---" for _ in cabecalho) + "|"]
    saida += ["| " + " | ".join(linha) + " |" for linha in linhas]
    return "\n".join(saida)
