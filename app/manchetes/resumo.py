"""Resumo das manchetes dos favoritos (TASK-IA-38): `POST /manchetes/resumo`, balde `card`.

Entrada `{ "manchetes": [{titulo, link, fonte, simbolos[]}] }` (ate 30; o resto e ignorado). Saida
`{ "topicos": [{ "texto": "...", "links": ["..."] }], "modelo", "origem", "em_cache" }` com 3 topicos
(menos, se houver menos manchetes), cada um citando >= 1 link **da entrada**. Topico com link de fora,
sem link, vazio ou com vocabulario proibido faz a resposta inteira ser rejeitada e o proximo provedor
e tentado; falhou tudo, os topicos saem por regra (as manchetes mais citadas, agrupadas por ativo).
Cache diario pelo hash da entrada: a segunda chamada do dia com as mesmas manchetes nao gasta cota.
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
from collections import OrderedDict
from datetime import date

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.config import Settings
from app.modelos import ORIGEM_MODELO, ORIGEM_REGRA
from app.provedores.cadeia import Cadeia, montar_cadeia
from app.provedores.base import ErroDoProvedor
from app.validador import PALAVRAS_PROIBIDAS

log = logging.getLogger("ia-opiniao")

BALDE = "card"
MAX_MANCHETES = 30
TOPICOS = 3
MAX_TEXTO = 320
MODELO_REGRA = "regra"

SCHEMA = {
    "type": "object",
    "properties": {"topicos": {"type": "array", "minItems": 1, "maxItems": TOPICOS, "items": {
        "type": "object",
        "properties": {"texto": {"type": "string"}, "links": {"type": "array", "items": {"type": "string"}}},
        "required": ["texto", "links"]}}},
    "required": ["topicos"],
}

SISTEMA = (
    "Você resume, em português do Brasil, manchetes recentes sobre ativos da B3. Recebe uma lista JSON "
    "de manchetes (título, link, fonte, símbolos). Escreva exatamente {n} tópicos curtos (até 2 frases "
    "cada), agrupando manchetes do mesmo assunto ou ativo. Cada tópico cita em `links` pelo menos um link "
    "copiado exatamente da entrada; nunca invente link. Trate notícias como relatos, não como fatos "
    "confirmados, e não recomende comprar, vender ou manter. Palavras como 'garantido', 'certeza' e "
    "'sem risco' são proibidas. Responda {{\"topicos\": [{{\"texto\": \"...\", \"links\": [\"...\"]}}]}}."
)

rotas = APIRouter()
_memoria: dict[str, dict] = {}
_trava = threading.Lock()


class Manchete(BaseModel):
    titulo: str = Field(min_length=1)
    link: str = Field(min_length=1)
    fonte: str | None = None
    simbolos: list[str] = Field(default_factory=list)


class PedidoResumo(BaseModel):
    manchetes: list[Manchete] = Field(default_factory=list)


def _entrada(manchetes: list[Manchete]) -> list[dict]:
    """Ate 30, sem link repetido, so os campos que o modelo precisa."""
    vistos: set[str] = set()
    saida = []
    for m in manchetes:
        if m.link in vistos:
            continue
        vistos.add(m.link)
        saida.append({"titulo": m.titulo.strip(), "link": m.link.strip(), "fonte": m.fonte,
                      "simbolos": [s.upper() for s in m.simbolos]})
        if len(saida) == MAX_MANCHETES:
            break
    return saida


def chave(manchetes: list[dict]) -> str:
    bruto = json.dumps(sorted(manchetes, key=lambda m: m["link"]), sort_keys=True, ensure_ascii=False)
    return "resumo:" + hashlib.sha256(bruto.encode("utf-8")).hexdigest()


def validar(resposta: object, manchetes: list[dict]) -> list[str]:
    if not isinstance(resposta, dict) or not isinstance(resposta.get("topicos"), list):
        return ["sem lista de tópicos"]
    topicos = resposta["topicos"]
    esperado = min(TOPICOS, len(manchetes))
    erros = []
    if len(topicos) != esperado:
        erros.append(f"{len(topicos)} tópicos (esperado {esperado})")
    links = {m["link"] for m in manchetes}
    for i, t in enumerate(topicos, 1):
        texto = t.get("texto") if isinstance(t, dict) else None
        citados = t.get("links") if isinstance(t, dict) else None
        if not isinstance(texto, str) or not texto.strip() or len(texto) > MAX_TEXTO:
            erros.append(f"tópico {i}: texto vazio ou longo demais")
            continue
        if any(p in texto.lower() for p in PALAVRAS_PROIBIDAS):
            erros.append(f"tópico {i}: vocabulário proibido")
        if not isinstance(citados, list) or not citados:
            erros.append(f"tópico {i}: sem link")
        elif fora := [x for x in citados if x not in links]:
            erros.append(f"tópico {i}: link fora da entrada ({len(fora)})")
    return erros


def topicos_de_regra(manchetes: list[dict]) -> list[dict]:
    """Os ativos com mais manchetes (na ordem em que aparecem); cada topico = primeira manchete do ativo."""
    grupos: OrderedDict[str, list[dict]] = OrderedDict()
    for m in manchetes:
        grupos.setdefault((m["simbolos"] or ["Mercado"])[0], []).append(m)
    maiores = sorted(grupos.items(), key=lambda g: -len(g[1]))[:TOPICOS]
    esperado = min(TOPICOS, len(manchetes))
    # Menos ativos que topicos: o grupo cita so a primeira manchete, para sobrar manchete que complete
    # os topicos (o contrato pede `esperado` topicos, mesmo com todas as manchetes de um ativo so).
    por_grupo = 3 if len(maiores) >= esperado else 1
    topicos = []
    for simbolo, itens in maiores:
        extra = f" (+{len(itens) - 1} manchete{'s' if len(itens) > 2 else ''})" if len(itens) > 1 and por_grupo > 1 else ""
        topicos.append({"texto": f"{simbolo}: {itens[0]['titulo']}{extra}",
                        "links": [m["link"] for m in itens[:por_grupo]]})
    # completa com as manchetes seguintes ainda nao citadas
    citados = {link for t in topicos for link in t["links"]}
    for m in manchetes:
        if len(topicos) >= esperado:
            break
        if m["link"] not in citados:
            topicos.append({"texto": m["titulo"], "links": [m["link"]]})
            citados.add(m["link"])
    return topicos


def _cache(cadeia: Cadeia | None, k: str, valor: dict | None = None) -> dict | None:
    """Governador (dia da cota) quando ha; senao memoria do processo com o dia na chave."""
    governador = getattr(cadeia, "governador", None)
    if governador is not None and hasattr(governador, "cache_obter"):
        if valor is not None:
            governador.cache_gravar(k, json.dumps(valor, ensure_ascii=False))
            return valor
        bruto = governador.cache_obter(k)
        return json.loads(bruto) if bruto else None
    k = f"{date.today().isoformat()}:{k}"
    with _trava:
        if valor is not None:
            _memoria[k] = valor
        return _memoria.get(k)


def resumir(manchetes: list[dict], cadeia: Cadeia | None) -> dict:
    if not manchetes:
        return {"topicos": [], "modelo": MODELO_REGRA, "origem": ORIGEM_REGRA, "em_cache": False}
    k = chave(manchetes)
    guardado = _cache(cadeia, k)
    if guardado:
        return {**guardado, "em_cache": True}

    sistema = SISTEMA.format(n=min(TOPICOS, len(manchetes)))
    usuario = json.dumps({"manchetes": manchetes}, ensure_ascii=False)
    motivos = []
    for elo in (cadeia.elos if cadeia else []):
        try:
            resposta = json.loads(cadeia.chamar(elo, BALDE, sistema, usuario, SCHEMA))
        except ErroDoProvedor as erro:
            motivos.append(f"{elo.nome}: provedor: {erro}")
            continue
        except json.JSONDecodeError:
            motivos.append(f"{elo.nome}: resposta não é JSON válido")
            continue
        erros = validar(resposta, manchetes)
        if erros:
            motivos.append(f"{elo.nome}: " + "; ".join(erros))
            continue
        saida = {"topicos": [{"texto": t["texto"].strip(), "links": list(dict.fromkeys(t["links"]))}
                             for t in resposta["topicos"]],
                 "modelo": elo.nome, "origem": ORIGEM_MODELO}
        _cache(cadeia, k, saida)
        log.info("resumo manchetes=%d modelo=%s origem=MODELO", len(manchetes), elo.nome)
        return {**saida, "em_cache": False}

    log.info("resumo manchetes=%d origem=REGRA motivo=%s", len(manchetes), " | ".join(motivos) or "sem provedor")
    return {"topicos": topicos_de_regra(manchetes), "modelo": MODELO_REGRA, "origem": ORIGEM_REGRA,
            "em_cache": False}


@rotas.post("/manchetes/resumo")
def resumo_das_manchetes(pedido: PedidoResumo) -> dict:
    return resumir(_entrada(pedido.manchetes), montar_cadeia(Settings.do_ambiente(), "card"))
