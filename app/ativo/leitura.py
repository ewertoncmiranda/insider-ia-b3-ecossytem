"""Leitura do ativo em linguagem natural (CTR-IA-04, TASK-IA-36): um paragrafo de 3 a 4 frases.

O modelo so redige a partir do pacote (CTR-IA-03); todo numero do texto tem de existir no pacote e o
vocabulario proibido do validador vale aqui tambem. Falhou tudo (sem cota, sem Gemini, texto
rejeitado): frases fixas montadas do proprio pacote, `origem = REGRA`. Cache por (ativo, pregao):
a segunda chamada no mesmo pregao nao gasta cota.
"""

from __future__ import annotations

import json
import logging
import re
import threading
from datetime import datetime, timezone

from app.modelos import ORIGEM_MODELO, ORIGEM_REGRA
from app.provedores.cadeia import Cadeia
from app.provedores.base import ErroDoProvedor
from app.validador import PALAVRAS_PROIBIDAS

log = logging.getLogger("ia-opiniao")

BALDE = "card"
MODELO_REGRA = "regra"
MIN_CARACTERES, MAX_CARACTERES = 80, 900
_NUMERO = re.compile(r"\d+(?:[.,]\d+)?")

SCHEMA = {"type": "object", "properties": {"texto": {"type": "string"}}, "required": ["texto"]}

SISTEMA = (
    "Você escreve, em português do Brasil, UM parágrafo de 3 a 4 frases sobre um ativo da B3, usando "
    "somente os dados do JSON recebido (cotação, fundamentos, sinais, opinião por horizonte, comunicados "
    "e manchetes). Descreva o quadro; não recomende comprar, vender ou manter. Não invente números: use só "
    "os que aparecem no JSON (variações estão em fração: 0.052 = 5,2%). Não cite notícias como fato "
    "confirmado. Palavras como 'garantido', 'certeza' e 'sem risco' são proibidas. "
    "Responda {\"texto\": \"...\"}."
)

_memoria: dict[str, dict] = {}
_trava = threading.Lock()


def _normalizar(numero: str) -> str:
    n = numero.replace(",", ".")
    return n.rstrip("0").rstrip(".") if "." in n else n


def numeros_permitidos(pacote: dict) -> set[str]:
    """Todo numero escrito no pacote, mais os arredondamentos e os percentuais das fracoes."""
    permitidos = {_normalizar(n) for n in _NUMERO.findall(json.dumps(pacote, ensure_ascii=False))}

    def visitar(valor) -> None:
        if isinstance(valor, dict):
            for v in valor.values():
                visitar(v)
        elif isinstance(valor, list):
            for v in valor:
                visitar(v)
        elif isinstance(valor, (int, float)) and not isinstance(valor, bool):
            for base in (abs(valor), abs(valor) * 100):
                for casas in (0, 1, 2):
                    permitidos.add(_normalizar(f"{base:.{casas}f}"))

    visitar(pacote)
    return permitidos


def validar_texto(texto: object, pacote: dict) -> list[str]:
    if not isinstance(texto, str):
        return ["texto ausente"]
    t = texto.strip()
    erros = []
    if not MIN_CARACTERES <= len(t) <= MAX_CARACTERES:
        erros.append(f"tamanho fora de {MIN_CARACTERES}-{MAX_CARACTERES} caracteres")
    proibidas = [p for p in PALAVRAS_PROIBIDAS if p in t.lower()]
    if proibidas:
        erros.append(f"vocabulário proibido: {proibidas}")
    permitidos = numeros_permitidos(pacote)
    sobra = sorted({_normalizar(n) for n in _NUMERO.findall(t)} - permitidos)
    if sobra:
        erros.append(f"número fora do pacote: {sobra}")
    return erros


def _pct(fracao: float | None) -> str | None:
    return None if fracao is None else f"{fracao * 100:.1f}".replace(".", ",") + "%"


def texto_de_regra(pacote: dict) -> str:
    """Frases fixas a partir do pacote; parte sem dado simplesmente nao entra."""
    s, cot, fund = pacote["simbolo"], pacote.get("cotacao") or {}, pacote.get("fundamentos") or {}
    frases = []
    if cot.get("fechamento") is not None:
        partes = [f"{s} fechou a R$ {cot['fechamento']:.2f}".replace(".", ",")]
        if _pct(cot.get("variacao_1m")):
            partes.append(f"variação de {_pct(cot['variacao_1m'])} em cerca de um mês")
        if _pct(cot.get("variacao_12m")):
            partes.append(f"{_pct(cot['variacao_12m'])} em 12 meses")
        frases.append(", ".join(partes) + ".")
    if fund.get("pl") is not None:
        frases.append(f"O P/L está em {fund['pl']:.1f}".replace(".", ",")
                      + (f" ({fund['classificacao_pl'].lower()})" if fund.get("classificacao_pl") else "") + ".")
    curto = next((o for o in pacote.get("opiniao") or [] if o.get("opiniao")), None)
    if curto:
        frases.append(f"A leitura por regra para {curto['horizonte_pregoes']} pregões é "
                      f"{curto['opiniao'].replace('_', ' ').lower()}, com {curto['risco'].replace('_', ' ').lower()}.")
    if pacote.get("sinais"):
        frases.append("Sinais mais fortes do dia: " + "; ".join(
            f"{x['rotulo']} ({x['valor']})" for x in pacote["sinais"]) + ".")
    return " ".join(frases) or f"Sem dados suficientes para descrever {s} agora."


def _cache_obter(cadeia: Cadeia | None, chave: str) -> dict | None:
    governador = getattr(cadeia, "governador", None)
    if governador is not None and hasattr(governador, "cache_obter"):
        bruto = governador.cache_obter(chave)
        return json.loads(bruto) if bruto else None
    with _trava:
        return _memoria.get(chave)


def _cache_gravar(cadeia: Cadeia | None, chave: str, valor: dict) -> None:
    governador = getattr(cadeia, "governador", None)
    if governador is not None and hasattr(governador, "cache_gravar"):
        governador.cache_gravar(chave, json.dumps(valor, ensure_ascii=False))
        return
    with _trava:
        _memoria[chave] = valor


def gerar_leitura(pacote: dict, cadeia: Cadeia | None) -> dict:
    """Saida do CTR-IA-04. So resposta do modelo vai para o cache: a de regra tenta o modelo de novo."""
    chave = f"leitura:{pacote['simbolo']}:{pacote.get('data_pregao')}"
    guardado = _cache_obter(cadeia, chave)
    if guardado:
        return {**guardado, "em_cache": True}

    usuario = json.dumps({k: v for k, v in pacote.items() if k != "aviso"}, ensure_ascii=False)
    motivos = []
    for elo in (cadeia.elos if cadeia else []):
        try:
            texto = json.loads(cadeia.chamar(elo, BALDE, SISTEMA, usuario, SCHEMA)).get("texto")
        except ErroDoProvedor as erro:
            motivos.append(f"{elo.nome}: provedor: {erro}")
            continue
        except (json.JSONDecodeError, AttributeError):
            motivos.append(f"{elo.nome}: resposta não é JSON válido")
            continue
        erros = validar_texto(texto, pacote)
        if erros:
            motivos.append(f"{elo.nome}: " + "; ".join(erros))
            continue
        saida = {"simbolo": pacote["simbolo"], "data_pregao": pacote.get("data_pregao"), "texto": texto.strip(),
                 "modelo": elo.nome, "origem": ORIGEM_MODELO,
                 "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        _cache_gravar(cadeia, chave, saida)
        log.info("leitura simbolo=%s modelo=%s origem=MODELO", pacote["simbolo"], elo.nome)
        return {**saida, "em_cache": False}

    log.info("leitura simbolo=%s origem=REGRA motivo=%s", pacote["simbolo"], " | ".join(motivos) or "sem provedor")
    return {"simbolo": pacote["simbolo"], "data_pregao": pacote.get("data_pregao"), "texto": texto_de_regra(pacote),
            "modelo": MODELO_REGRA, "origem": ORIGEM_REGRA,
            "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"), "em_cache": False}
