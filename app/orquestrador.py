"""Orquestrador: chama o modelo so quando ha o que escolher, valida e cai na regra se preciso.

Fluxo (SPEC 4.2): pedido -> (permitidas so SEM_BASE? regra) -> modelo (ate 2 tentativas, a segunda
com os erros da primeira) -> validador -> resposta | reserva por regra. Nenhuma excecao do provedor
sobe: sem Ollama, o servico continua respondendo (origem REGRA).
"""

from __future__ import annotations

import json
import logging

from app.contexto import FonteDeContexto, TrechoDeContexto, limitar
from app.modelos import (ORIGEM_MODELO, ORIGEM_REGRA, SEM_BASE, CotaDaResposta, ItemOpiniaoAtivo, PedidoOpiniao,
                          PedidoOpiniaoAtivo, RespostaOpiniao, RespostaOpiniaoAtivo)
from app.prompt import (INSTRUCAO_DO_ATIVO, SCHEMA_DA_RESPOSTA, SISTEMA, montar_mensagem, montar_mensagem_ativo,
                        schema_do_ativo)
from app.provedores.ollama import ErroDoProvedor, ProvedorLLM
from app.regras import resposta_de_regra
from app.validador import validar

TENTATIVAS = 2
MODELO_REGRA = "regra"

log = logging.getLogger("ia-opiniao")


def _fontes(justificativa: list[dict], trechos: list[TrechoDeContexto]) -> list[str]:
    """Fichas (caminho#secao) dos trechos citados, sem repetir e na ordem da justificativa."""
    fonte_de = {t.trecho_id: t.fonte for t in trechos}
    vistas: list[str] = []
    for item in justificativa:
        fonte = fonte_de.get(str(item.get("trecho_id") or ""))
        if fonte and fonte not in vistas:
            vistas.append(fonte)
    return vistas


def _com_fontes(justificativa: list[dict], trechos: list[TrechoDeContexto]) -> list[dict]:
    """Item com trecho_id ganha `fonte` e `trecho` (texto citado), congelados junto da opiniao."""
    por_id = {t.trecho_id: t for t in trechos}
    saida = []
    for item in justificativa:
        t = por_id.get(str(item.get("trecho_id") or ""))
        saida.append({**item, "fonte": t.fonte, "trecho": t.texto} if t else item)
    return saida


def _consultar(provedor: ProvedorLLM, pedido: PedidoOpiniao, sistema: str, schema: dict,
               trechos: list[TrechoDeContexto]) -> tuple[dict | None, int, str]:
    """(resposta valida | None, tentativas feitas, motivo da reserva quando None)."""
    mensagem = montar_mensagem(pedido, trechos)
    erros: list[str] = []
    for tentativa in range(1, TENTATIVAS + 1):
        usuario = mensagem if not erros else (
            mensagem + "\n\nSua resposta anterior foi rejeitada: " + "; ".join(erros)
            + ". Corrija e responda de novo.")
        try:
            bruto = provedor.gerar(sistema, usuario, schema)
        except ErroDoProvedor as erro:
            return None, tentativa, f"provedor: {erro}"
        try:
            resposta = json.loads(bruto)
        except json.JSONDecodeError:
            erros = ["resposta não é JSON válido"]
            continue
        valida, erros = validar(resposta, pedido, trechos)
        if valida is not None:
            return valida, tentativa, ""
    return None, TENTATIVAS, "rejeitada: " + "; ".join(erros)


def _trechos_do_ativo(pedidos: list[PedidoOpiniao], contexto: FonteDeContexto | None) -> list[TrechoDeContexto]:
    """Trechos de todos os horizontes, sem repetir, no mesmo limite de um pedido v1.0."""
    if contexto is None:
        return []
    vistos: dict[str, TrechoDeContexto] = {}
    for pedido in pedidos:
        for t in contexto.trechos(pedido):
            vistos.setdefault(t.trecho_id, t)
    return limitar(list(vistos.values()))


def _resposta(pedido: PedidoOpiniao, corpo: dict, trechos: list[TrechoDeContexto], modelo: str,
              skills_versao: str, origem: str, tentativas: int) -> RespostaOpiniao:
    ausentes = list(pedido.dados_ausentes) + ([pedido.motivo_sem_base] if pedido.motivo_sem_base else [])
    return RespostaOpiniao(
        opiniao=corpo["opiniao"], risco=corpo["risco"], justificativa=_com_fontes(corpo["justificativa"], trechos),
        o_que_invalida=corpo["o_que_invalida"], dados_ausentes=ausentes, fontes=_fontes(corpo["justificativa"], trechos),
        modelo=modelo, skills_versao=skills_versao, origem=origem, tentativas=tentativas,
    )


def opinar_ativo(pedido: PedidoOpiniaoAtivo, provedor: ProvedorLLM | None, skills_versao: str,
                 sistema: str | None = None, schema_do_item: dict | None = None,
                 contexto: FonteDeContexto | None = None) -> RespostaOpiniaoAtivo:
    """CTR-IA-01 v1.1: uma chamada ao modelo para os horizontes do ativo, validada item a item.

    Item ausente ou rejeitado cai na regra so para aquele horizonte (quando a cadeia de provedores
    existir, TASK-IA-26, vai ao proximo provedor antes). Horizonte que so permite SEM_BASE nao vai ao
    modelo. Sem segunda tentativa: refazer custaria outra chamada inteira (e cota, no Gemini).
    """
    pedidos = [pedido.do_horizonte(h) for h in pedido.horizontes]
    ao_modelo = [p for p in pedidos if list(p.permitidas) != [SEM_BASE]]
    nome_modelo = provedor.nome if provedor is not None else MODELO_REGRA
    trechos: list[TrechoDeContexto] = []
    validos: dict[int, dict] = {}
    motivos: dict[int, str] = {}

    if provedor is None:
        motivos = {p.horizonte_pregoes: "sem provedor" for p in ao_modelo}
    elif ao_modelo:
        trechos = _trechos_do_ativo(ao_modelo, contexto)
        itens, motivo = None, "sem lista de itens"
        try:
            bruto = provedor.gerar((sistema or SISTEMA) + INSTRUCAO_DO_ATIVO, montar_mensagem_ativo(ao_modelo, trechos),
                                   schema_do_ativo(schema_do_item or SCHEMA_DA_RESPOSTA))
            itens = json.loads(bruto).get("itens")
        except ErroDoProvedor as erro:
            motivo = f"provedor: {erro}"
        except (json.JSONDecodeError, AttributeError):
            motivo = "resposta não é JSON válido"
        if not isinstance(itens, list):
            motivos = {p.horizonte_pregoes: motivo for p in ao_modelo}
        else:
            por_horizonte = {i.get("horizonte_pregoes"): i for i in itens if isinstance(i, dict)}
            for p in ao_modelo:
                item = por_horizonte.get(p.horizonte_pregoes)
                if item is None:
                    motivos[p.horizonte_pregoes] = "horizonte ausente na resposta"
                    continue
                valido, erros = validar(item, p, trechos)
                if valido is None:
                    motivos[p.horizonte_pregoes] = "rejeitada: " + "; ".join(erros)
                else:
                    validos[p.horizonte_pregoes] = valido

    saida: list[ItemOpiniaoAtivo] = []
    for p in pedidos:
        h = p.horizonte_pregoes
        if h in validos:
            r = _resposta(p, validos[h], trechos, nome_modelo, skills_versao, ORIGEM_MODELO, 1)
        else:
            motivos.setdefault(h, "só SEM_BASE permitido")
            # A linha diz quem respondeu: aqui foi a regra, mesmo que o modelo tenha sido chamado.
            chamou = provedor is not None and h in {q.horizonte_pregoes for q in ao_modelo}
            r = _resposta(p, resposta_de_regra(p), [], MODELO_REGRA, skills_versao, ORIGEM_REGRA, int(chamou))
        log.info("opiniao simbolo=%s horizonte=%d skills=%s modelo=%s origem=%s motivo=%s",
                 p.simbolo, h, skills_versao, r.modelo, r.origem, motivos.get(h, "-"))
        saida.append(ItemOpiniaoAtivo(horizonte_pregoes=h, **r.model_dump()))

    # Sem governador de cota ainda (TASK-IA-25): o Gemini nao existe neste servico, logo indisponivel.
    return RespostaOpiniaoAtivo(simbolo=pedido.simbolo, data_pregao=pedido.data_pregao, modelo=nome_modelo,
                                skills_versao=skills_versao, itens=saida,
                                cota=CotaDaResposta(balde=pedido.uso, restante_hoje=None, gemini_disponivel=False))


def opinar(pedido: PedidoOpiniao, provedor: ProvedorLLM | None, skills_versao: str,
           sistema: str | None = None, schema: dict | None = None,
           contexto: FonteDeContexto | None = None) -> RespostaOpiniao:
    """`sistema` e `schema` vem das skills selecionadas (TASK-IA-04); sem skills, o prompt embutido."""
    origem, tentativas, motivo = ORIGEM_REGRA, 0, ""
    nome_modelo = provedor.nome if provedor is not None else MODELO_REGRA
    corpo: dict | None = None
    trechos: list[TrechoDeContexto] = []
    if provedor is None:
        motivo = "sem provedor"
    elif list(pedido.permitidas) == [SEM_BASE]:
        motivo = "só SEM_BASE permitido"  # nada a escolher: dispensa a chamada
    else:
        trechos = limitar(contexto.trechos(pedido)) if contexto is not None else []
        corpo, tentativas, motivo = _consultar(provedor, pedido, sistema or SISTEMA,
                                               schema or SCHEMA_DA_RESPOSTA, trechos)
        if corpo is not None:
            origem = ORIGEM_MODELO
    if corpo is None:
        corpo = resposta_de_regra(pedido)
    log.info("opiniao simbolo=%s horizonte=%d skills=%s modelo=%s origem=%s tentativas=%d motivo=%s",
             pedido.simbolo, pedido.horizonte_pregoes, skills_versao, nome_modelo, origem, tentativas,
             motivo or "-")
    ausentes = list(pedido.dados_ausentes) + ([pedido.motivo_sem_base] if pedido.motivo_sem_base else [])
    return RespostaOpiniao(
        opiniao=corpo["opiniao"], risco=corpo["risco"], justificativa=_com_fontes(corpo["justificativa"], trechos),
        o_que_invalida=corpo["o_que_invalida"], dados_ausentes=ausentes, fontes=_fontes(corpo["justificativa"], trechos),
        modelo=nome_modelo, skills_versao=skills_versao, origem=origem, tentativas=tentativas,
    )
