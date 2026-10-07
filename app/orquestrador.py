"""Orquestrador: chama o modelo so quando ha o que escolher, valida e cai na regra se preciso.

Fluxo (SPEC 4.2): pedido -> (permitidas so SEM_BASE? regra) -> modelo (ate 2 tentativas, a segunda
com os erros da primeira) -> validador -> resposta | reserva por regra. Nenhuma excecao do provedor
sobe: sem Ollama, o servico continua respondendo (origem REGRA).
"""

from __future__ import annotations

import json
import logging

from app.modelos import ORIGEM_MODELO, ORIGEM_REGRA, SEM_BASE, PedidoOpiniao, RespostaOpiniao
from app.prompt import SCHEMA_DA_RESPOSTA, SISTEMA, montar_mensagem
from app.provedores.ollama import ErroDoProvedor, ProvedorLLM
from app.regras import resposta_de_regra
from app.validador import validar

TENTATIVAS = 2
MODELO_REGRA = "regra"

log = logging.getLogger("ia-opiniao")


def _consultar(provedor: ProvedorLLM, pedido: PedidoOpiniao) -> tuple[dict | None, int, str]:
    """(resposta valida | None, tentativas feitas, motivo da reserva quando None)."""
    mensagem = montar_mensagem(pedido)
    erros: list[str] = []
    for tentativa in range(1, TENTATIVAS + 1):
        usuario = mensagem if not erros else (
            mensagem + "\n\nSua resposta anterior foi rejeitada: " + "; ".join(erros)
            + ". Corrija e responda de novo.")
        try:
            bruto = provedor.gerar(SISTEMA, usuario, SCHEMA_DA_RESPOSTA)
        except ErroDoProvedor as erro:
            return None, tentativa, f"provedor: {erro}"
        try:
            resposta = json.loads(bruto)
        except json.JSONDecodeError:
            erros = ["resposta não é JSON válido"]
            continue
        valida, erros = validar(resposta, pedido)
        if valida is not None:
            return valida, tentativa, ""
    return None, TENTATIVAS, "rejeitada: " + "; ".join(erros)


def opinar(pedido: PedidoOpiniao, provedor: ProvedorLLM | None, skills_versao: str) -> RespostaOpiniao:
    origem, tentativas, motivo = ORIGEM_REGRA, 0, ""
    nome_modelo = provedor.nome if provedor is not None else MODELO_REGRA
    corpo: dict | None = None
    if provedor is None:
        motivo = "sem provedor"
    elif list(pedido.permitidas) == [SEM_BASE]:
        motivo = "só SEM_BASE permitido"  # nada a escolher: dispensa a chamada
    else:
        corpo, tentativas, motivo = _consultar(provedor, pedido)
        if corpo is not None:
            origem = ORIGEM_MODELO
    if corpo is None:
        corpo = resposta_de_regra(pedido)
    log.info("opiniao simbolo=%s horizonte=%d skills=%s modelo=%s origem=%s tentativas=%d motivo=%s",
             pedido.simbolo, pedido.horizonte_pregoes, skills_versao, nome_modelo, origem, tentativas,
             motivo or "-")
    ausentes = list(pedido.dados_ausentes) + ([pedido.motivo_sem_base] if pedido.motivo_sem_base else [])
    return RespostaOpiniao(
        opiniao=corpo["opiniao"], risco=corpo["risco"], justificativa=corpo["justificativa"],
        o_que_invalida=corpo["o_que_invalida"], dados_ausentes=ausentes, fontes=[],
        modelo=nome_modelo, skills_versao=skills_versao, origem=origem, tentativas=tentativas,
    )
