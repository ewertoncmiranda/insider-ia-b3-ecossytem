"""Validador da resposta do modelo (REQ-IA-03).

A resposta so vale se: opiniao dentro das permitidas, risco igual ao calculado, cada item de
justificativa citando uma evidencia real, nenhum numero fora da entrada, sem vocabulario de
promessa e no maximo 5 itens. `o_que_invalida` nao e do modelo: sai de `condicoes_contrarias`.
"""

from __future__ import annotations

import re

from app.contexto import TrechoDeContexto
from app.modelos import NEGATIVO, OPINIOES, POSITIVO, RISCOS, SEM_BASE, Evidencia, PedidoOpiniao
from app.regras import MAXIMO_DE_JUSTIFICATIVAS, condicoes_contrarias

PALAVRAS_PROIBIDAS = ("garantido", "garantida", "certeza", "sem risco", "não tem como perder",
                      "imperdível", "compre", "venda agora", "vai subir", "vai cair",
                      "bom investimento", "boa oportunidade", "oportunidade de")

LIMITE_LEITURA = 200
LIMITE_INVALIDA = 160
MINIMO_DE_PALAVRAS_INVALIDA = 3

_NUMERO = re.compile(r"\d+(?:[.,]\d+)?")
_ID_TECNICO = re.compile(r"[a-z]+_[a-z0-9_]+")


def _item(j: dict) -> dict:
    if j.get("evidencia_id"):
        return {"evidencia_id": str(j["evidencia_id"]), "leitura": str(j["leitura"]).strip()}
    return {"trecho_id": str(j["trecho_id"]), "leitura": str(j["leitura"]).strip()}


def _numeros(texto: str) -> set[str]:
    return {n.replace(",", ".") for n in _NUMERO.findall(texto)}


def validar(resposta: object, pedido: PedidoOpiniao,
            trechos: list[TrechoDeContexto] | None = None) -> tuple[dict | None, list[str]]:
    """(resposta normalizada, erros). Erros vazios = valida."""
    erros: list[str] = []
    if not isinstance(resposta, dict):
        return None, ["resposta não é um objeto JSON"]
    opiniao, risco = resposta.get("opiniao"), resposta.get("risco")
    # Se um modelo mandar `o_que_invalida` mesmo assim, ele e ignorado, mas tem de ser lista de textos.
    justificativa, invalida = resposta.get("justificativa"), resposta.get("o_que_invalida") or []

    if opiniao not in OPINIOES:
        erros.append(f"opiniao inválida: {opiniao!r}")
    elif opiniao not in pedido.permitidas:
        erros.append(f"opiniao {opiniao} fora das permitidas {list(pedido.permitidas)}")
    if risco not in RISCOS:
        erros.append(f"risco inválido: {risco!r}")
    elif risco != pedido.risco_calculado:
        erros.append(f"risco {risco} difere do calculado {pedido.risco_calculado}")
    if not isinstance(justificativa, list) or not all(isinstance(j, dict) for j in justificativa):
        erros.append("justificativa deve ser uma lista de objetos")
        justificativa = []
    if not isinstance(invalida, list) or not all(isinstance(i, str) for i in invalida):
        erros.append("o_que_invalida deve ser uma lista de textos")
        invalida = []
    if erros:
        return None, erros

    por_id: dict[str, Evidencia] = {e.id: e for e in pedido.evidencias}
    por_trecho = {t.trecho_id: t for t in (trechos or [])}
    permitidos = {n for e in pedido.evidencias for n in _numeros(f"{e.valor} {e.rotulo}")}
    if opiniao != SEM_BASE and not justificativa:
        erros.append("opinião sem justificativa")
    citadas: list[Evidencia] = []
    for item in justificativa:
        leitura = str(item.get("leitura") or "").strip()
        trecho_id = item.get("trecho_id")
        if trecho_id and not item.get("evidencia_id"):
            trecho = por_trecho.get(str(trecho_id))
            if trecho is None:
                erros.append(f"trecho inexistente: {trecho_id!r}")
                continue
            if not leitura or len(leitura) > LIMITE_LEITURA:
                erros.append(f"leitura vazia ou longa demais em {trecho.trecho_id}")
            sobra = _numeros(leitura) - _numeros(trecho.texto) - permitidos
            if sobra:
                erros.append(f"número fora do trecho {trecho.trecho_id}: {sorted(sobra)}")
            continue
        ev = por_id.get(str(item.get("evidencia_id")))
        if ev is None:
            erros.append(f"evidência inexistente: {item.get('evidencia_id')!r}")
            continue
        citadas.append(ev)
        if not leitura or len(leitura) > LIMITE_LEITURA:
            erros.append(f"leitura vazia ou longa demais em {ev.id}")
        sobra = _numeros(leitura) - permitidos
        if sobra:
            erros.append(f"número fora do dossiê em {ev.id}: {sorted(sobra)}")
    if opiniao == POSITIVO and not any(e.direcao > 0 for e in citadas):
        erros.append("SINAL_POSITIVO sem citar evidência favorável")
    if opiniao == NEGATIVO and not any(e.direcao < 0 for e in citadas):
        erros.append("SINAL_NEGATIVO sem citar evidência desfavorável")
    juntos = " ".join([str(j.get("leitura", "")) for j in justificativa] + invalida).lower()
    achadas = [p for p in PALAVRAS_PROIBIDAS if p in juntos]
    if achadas:
        erros.append(f"vocabulário proibido: {achadas}")
    if len(justificativa) > MAXIMO_DE_JUSTIFICATIVAS:
        erros.append(f"justificativa: no máximo {MAXIMO_DE_JUSTIFICATIVAS} itens")
    # "O que invalida" e uma condicao futura, nao a repeticao de uma evidencia ou de um id.
    nomes = [t.lower() for e in pedido.evidencias for t in (e.rotulo, e.id)]
    if any(n in i.lower() for i in invalida for n in nomes) or any(_ID_TECNICO.search(i) for i in invalida):
        erros.append("o_que_invalida repete uma evidência em vez de dar uma condição")
    if len(invalida) > 3 or any(len(i) > LIMITE_INVALIDA for i in invalida):
        erros.append("o_que_invalida: máximo 3 itens curtos")
    if any(len(i.split()) < MINIMO_DE_PALAVRAS_INVALIDA for i in invalida):
        erros.append("o_que_invalida deve ter frases, não ids")
    if erros:
        return None, erros
    return {
        "opiniao": opiniao,
        "risco": risco,
        "justificativa": [_item(j) for j in justificativa],
        "o_que_invalida": condicoes_contrarias(pedido, str(opiniao)),
    }, []
