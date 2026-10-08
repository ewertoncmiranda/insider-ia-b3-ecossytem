"""Rotas do ativo (CTR-IA-03/04). O painel chama com o prefixo /ia, que o proxy dele remove."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.ativo.cliente_gestor import AtivoNaoEncontrado, GestorIndisponivel, SimboloInvalido
from app.ativo.leitura import gerar_leitura
from app.ativo.pacote import pacote
from app.config import Settings
from app.provedores.cadeia import montar_cadeia

rotas = APIRouter()


def _pacote_ou_erro(simbolo: str) -> dict:
    try:
        return pacote(simbolo)
    except SimboloInvalido as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from erro
    except AtivoNaoEncontrado as erro:
        raise HTTPException(status_code=404, detail=f"ativo sem dados no gestor: {simbolo}") from erro
    except GestorIndisponivel as erro:
        raise HTTPException(status_code=503, detail="gestor indisponível; tente de novo em instantes") from erro


@rotas.get("/ativo/{simbolo}")
def pacote_do_ativo(simbolo: str) -> dict:
    """CTR-IA-03: so leitura, sem cota, cache de 15 minutos por ativo."""
    return _pacote_ou_erro(simbolo)


@rotas.post("/ativo/{simbolo}/leitura")
def leitura_do_ativo(simbolo: str) -> dict:
    """CTR-IA-04: paragrafo de 3-4 frases (balde `card`), cache por pregao; sem modelo, frases de regra."""
    dados = _pacote_ou_erro(simbolo)
    return gerar_leitura(dados, montar_cadeia(Settings.do_ambiente(), "card"))
