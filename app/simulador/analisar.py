"""Analise IA_LIVRE para o Simulador de Operacoes (SIM-IA-1): `POST /simulador/analisar`.

Recebe os resultados das 7 estrategias de um ativo e devolve uma analise objetiva do Gemini
(comprar / manter / sair + razao), sem guards regulatorios. O resultado e puramente analitico
e nao gera ordem real. Cache diario pelo hash da entrada — segunda chamada do mesmo dia nao
gasta cota.
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
from datetime import date
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.config import Settings
from app.modelos import ORIGEM_MODELO, ORIGEM_REGRA
from app.provedores.base import ErroDoProvedor
from app.provedores.cadeia import Cadeia, montar_cadeia

log = logging.getLogger("ia-opiniao")

BALDE = "card"
MAX_TEXTO = 600
MODELO_REGRA = "regra"

SCHEMA = {
    "type": "object",
    "properties": {"analise": {"type": "string", "minLength": 10, "maxLength": MAX_TEXTO}},
    "required": ["analise"],
}

SISTEMA = (
    "Voce analisa ativos da B3 com base em resultados quantitativos de estrategias de investimento. "
    "Recebera o simbolo do ativo e os quintis e retornos de 7 estrategias. "
    "Responda com uma analise objetiva de 3 a 5 frases: qual o posicionamento sugerido "
    "(comprar / manter / sair), por que as estrategias convergem ou divergem, e qual o risco principal. "
    "Nao use linguagem vaga. Nao invente dados alem do que foi fornecido. "
    'Responda {"analise": "texto direto aqui"}.'
)

rotas = APIRouter()
_memoria: dict[str, dict] = {}
_trava = threading.Lock()


class ResultadoEstrategia(BaseModel):
    versao: str = Field(min_length=1)
    quintil: Optional[int] = None
    retorno_pct: Optional[float] = None


class PedidoAnalisarSimulador(BaseModel):
    simbolo: str = Field(min_length=1, max_length=10)
    resultados: list[ResultadoEstrategia] = Field(min_length=1)


def _chave(simbolo: str, resultados: list[dict]) -> str:
    bruto = json.dumps(
        {"simbolo": simbolo.upper(), "resultados": sorted(resultados, key=lambda r: r["versao"])},
        sort_keys=True, ensure_ascii=False,
    )
    return "simulador:" + hashlib.sha256(bruto.encode("utf-8")).hexdigest()


def _cache(cadeia: Cadeia | None, k: str, valor: dict | None = None) -> dict | None:
    governador = getattr(cadeia, "governador", None)
    if governador is not None and hasattr(governador, "cache_obter"):
        if valor is not None:
            governador.cache_gravar(k, json.dumps(valor, ensure_ascii=False))
            return valor
        bruto = governador.cache_obter(k)
        return json.loads(bruto) if bruto else None
    k_dia = f"{date.today().isoformat()}:{k}"
    with _trava:
        if valor is not None:
            _memoria[k_dia] = valor
        return _memoria.get(k_dia)


def _validar(resposta: object) -> str | None:
    if not isinstance(resposta, dict):
        return "resposta nao e objeto JSON"
    texto = resposta.get("analise")
    if not isinstance(texto, str) or not texto.strip():
        return "campo 'analise' ausente ou vazio"
    if len(texto) > MAX_TEXTO:
        return f"analise com {len(texto)} chars (maximo {MAX_TEXTO})"
    return None


def _analise_regra(simbolo: str, resultados: list[dict]) -> str:
    """Fallback sem modelo: resume convergencia pelos quintis."""
    q_bom = [r["versao"] for r in resultados if (r.get("quintil") or 99) <= 2]
    q_ruim = [r["versao"] for r in resultados if (r.get("quintil") or 0) >= 4]
    if len(q_bom) >= 4:
        return (f"{simbolo}: maioria das estrategias em Q1-Q2 ({', '.join(q_bom)}). "
                "Sinal analitico favoravel. Modelo IA indisponivel no momento.")
    if len(q_ruim) >= 4:
        return (f"{simbolo}: maioria das estrategias em Q4-Q5 ({', '.join(q_ruim)}). "
                "Sinal analitico desfavoravel. Modelo IA indisponivel no momento.")
    return (f"{simbolo}: estrategias divergem (favoraveis: {len(q_bom)}, desfavoraveis: {len(q_ruim)}). "
            "Sem consenso claro. Modelo IA indisponivel no momento.")


def analisar(simbolo: str, resultados: list[dict], cadeia: Cadeia | None) -> dict:
    k = _chave(simbolo, resultados)
    guardado = _cache(cadeia, k)
    if guardado:
        return {**guardado, "em_cache": True}

    usuario = json.dumps(
        {"simbolo": simbolo.upper(), "resultados": resultados},
        ensure_ascii=False,
    )
    motivos = []
    for elo in (cadeia.elos if cadeia else []):
        try:
            resposta = json.loads(cadeia.chamar(elo, BALDE, SISTEMA, usuario, SCHEMA))
        except ErroDoProvedor as erro:
            motivos.append(f"{elo.nome}: provedor: {erro}")
            continue
        except json.JSONDecodeError:
            motivos.append(f"{elo.nome}: resposta nao e JSON valido")
            continue
        erro = _validar(resposta)
        if erro:
            motivos.append(f"{elo.nome}: {erro}")
            continue
        saida = {"analise": resposta["analise"].strip(), "modelo": elo.nome,
                 "origem": ORIGEM_MODELO, "tokens_usados": None}
        _cache(cadeia, k, saida)
        log.info("simulador analise simbolo=%s modelo=%s", simbolo, elo.nome)
        return {**saida, "em_cache": False}

    log.info("simulador analise simbolo=%s origem=REGRA motivo=%s",
             simbolo, " | ".join(motivos) or "sem provedor")
    return {"analise": _analise_regra(simbolo, resultados), "modelo": MODELO_REGRA,
            "origem": ORIGEM_REGRA, "tokens_usados": 0, "em_cache": False}


@rotas.post("/simulador/analisar")
def analisar_simulador(pedido: PedidoAnalisarSimulador) -> dict:
    resultados = [r.model_dump() for r in pedido.resultados]
    return analisar(pedido.simbolo, resultados, montar_cadeia(Settings.do_ambiente(), BALDE))
