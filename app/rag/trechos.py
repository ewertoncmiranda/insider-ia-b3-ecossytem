"""Fatia as fichas .md em trechos citaveis. Puro.

Cada secao (`## Titulo`) vira um trecho `"<ficha>#<secao>"`; a tabela da secao
"Por ano" vira um trecho por linha (`"<ficha>#por-ano/<ano>"`), com o
cabecalho junto, porque cada ano fica publico numa data diferente: a coluna
"Disp." da ficha. Os demais trechos herdam o `disponivel_ate` da ficha.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


@dataclass(frozen=True)
class Trecho:
    trecho_id: str
    texto: str
    fonte: str
    tipo: str
    simbolo: str | None
    setor: str | None
    disponivel_ate: date
    pontuacao: float = 0.0

    def hash(self) -> str:
        base = "\x1f".join([self.trecho_id, self.texto, self.fonte, self.tipo, self.simbolo or "",
                            self.setor or "", self.disponivel_ate.isoformat()])
        return hashlib.sha256(base.encode("utf-8")).hexdigest()


def slug(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", sem_acento.lower()).strip("-")


def ler_cabecalho(texto: str) -> tuple[dict, str]:
    """(cabecalho YAML minimo, corpo). So escalares e listas [a, b] - o formato
    que app/fichas/ficha.py escreve."""
    if not texto.startswith("---\n"):
        return {}, texto
    fim = texto.index("\n---\n", 4)
    cabecalho = {}
    for linha in texto[4:fim].splitlines():
        if ":" not in linha:
            continue
        chave, valor = linha.split(":", 1)
        valor = valor.strip()
        if valor.startswith("[") and valor.endswith("]"):
            cabecalho[chave.strip()] = [v.strip() for v in valor[1:-1].split(",") if v.strip()]
        else:
            if len(valor) >= 2 and valor[0] == valor[-1] == '"':
                valor = valor[1:-1].replace('\\"', '"').replace("\\\\", "\\")
            cabecalho[chave.strip()] = valor
    return cabecalho, texto[fim + 5:]


def _data(valor: str | None) -> date | None:
    if not valor:
        return None
    for formato in ("%Y-%m-%d", "%d/%m/%y", "%d/%m/%Y"):
        try:
            return datetime.strptime(valor.strip(), formato).date()
        except ValueError:
            continue
    return None


def secoes(corpo: str) -> list[tuple[str, str]]:
    partes = re.split(r"^## (.+)$", corpo, flags=re.M)
    return [(partes[i].strip(), partes[i + 1].strip()) for i in range(1, len(partes) - 1, 2)]


def da_ficha(caminho_relativo: str, texto: str) -> list[Trecho]:
    """caminho_relativo: relativo a conhecimento/, ex. 'ativos/PETR4.md'."""
    cabecalho, corpo = ler_cabecalho(texto)
    base_id = caminho_relativo.removesuffix(".md")
    fonte = f"conhecimento/{caminho_relativo}"
    tipo = cabecalho.get("tipo") or caminho_relativo.split("/", 1)[0]
    simbolo = cabecalho.get("simbolo") or None
    setor = cabecalho.get("setor") or None
    disponivel_ficha = _data(cabecalho.get("disponivel_ate")) or _data(cabecalho.get("gerado_em")) or date.max
    rotulo = " · ".join(x for x in (tipo, simbolo, setor, cabecalho.get("evidencia"), cabecalho.get("ano")) if x)

    saida: list[Trecho] = []
    for titulo, conteudo in secoes(corpo):
        secao = slug(titulo)
        if secao == "por-ano" and "|" in conteudo:
            saida += _linhas_por_ano(base_id, fonte, tipo, simbolo, setor, rotulo, conteudo, disponivel_ficha)
            continue
        saida.append(Trecho(f"{base_id}#{secao}", f"[{rotulo}] {titulo}\n{conteudo}", f"{fonte}#{secao}",
                            tipo, simbolo, setor, disponivel_ficha))
    return saida


def _linhas_por_ano(base_id, fonte, tipo, simbolo, setor, rotulo, conteudo, disponivel_ficha) -> list[Trecho]:
    linhas = [l for l in conteudo.splitlines() if l.startswith("|")]
    if len(linhas) < 3:
        return []
    cabecalho = [c.strip() for c in linhas[0].strip("|").split("|")]
    indice_disp = cabecalho.index("Disp.") if "Disp." in cabecalho else None
    saida = []
    for linha in linhas[2:]:
        celulas = [c.strip() for c in linha.strip("|").split("|")]
        ano = celulas[0]
        disponivel = (_data(celulas[indice_disp]) if indice_disp is not None else None)
        if disponivel is None:
            disponivel = disponivel_ficha if not ano.isdigit() else max(date(int(ano), 12, 31),
                                                                       min(disponivel_ficha, date(int(ano) + 1, 12, 31)))
        texto = f"[{rotulo}] Por ano — {ano}\n{linhas[0]}\n{linhas[1]}\n{linha}"
        saida.append(Trecho(f"{base_id}#por-ano/{ano}", texto, f"{fonte}#por-ano", tipo, simbolo, setor, disponivel))
    return saida


def do_diretorio(raiz: Path) -> list[Trecho]:
    trechos = []
    for arquivo in sorted(raiz.rglob("*.md")):
        relativo = arquivo.relative_to(raiz).as_posix()
        if relativo.startswith((".", "_")) or "/." in relativo:
            continue
        trechos += da_ficha(relativo, arquivo.read_text(encoding="utf-8"))
    return trechos
