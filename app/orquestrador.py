"""Orquestrador: chama o modelo so quando ha o que escolher, valida e cai na regra se preciso.

Fluxo (SPEC 4.2/13.2): pedido -> (permitidas so SEM_BASE? regra) -> cadeia de provedores (Gemini ->
Ollama, ate 2 tentativas so no local) -> validador -> resposta | reserva por regra. Nenhuma excecao do provedor
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
from app.provedores.cadeia import GEMINI, Cadeia, como_cadeia
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


def _consultar(cadeia: Cadeia, balde: str, pedido: PedidoOpiniao, sistema: str, schema: dict,
               trechos: list[TrechoDeContexto]) -> tuple[dict | None, int, str, str]:
    """(resposta valida | None, tentativas feitas, motivo da reserva, modelo que respondeu).

    Percorre os elos da cadeia (TASK-IA-26): falha, recusa de cota ou resposta rejeitada passa ao
    proximo. So o elo com `segunda_tentativa` (o local) refaz com os erros da primeira.
    """
    mensagem = montar_mensagem(pedido, trechos)
    tentativas, motivos = 0, []
    for elo in cadeia.elos:
        erros: list[str] = []
        for _ in range(TENTATIVAS if elo.segunda_tentativa else 1):
            usuario = mensagem if not erros else (
                mensagem + "\n\nSua resposta anterior foi rejeitada: " + "; ".join(erros)
                + ". Corrija e responda de novo.")
            tentativas += 1
            try:
                bruto = cadeia.chamar(elo, balde, sistema, usuario, schema)
            except ErroDoProvedor as erro:
                erros = [f"provedor: {erro}"]
                break
            try:
                resposta = json.loads(bruto)
            except json.JSONDecodeError:
                erros = ["resposta não é JSON válido"]
                continue
            valida, erros = validar(resposta, pedido, trechos)
            if valida is not None:
                return valida, tentativas, "", elo.nome
        motivos.append(f"{elo.nome}: " + "; ".join(erros))
    return None, tentativas, " | ".join(motivos), ""

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


def opinar_ativo(pedido: PedidoOpiniaoAtivo, provedor: ProvedorLLM | Cadeia | None, skills_versao: str,
                 sistema: str | None = None, schema_do_item: dict | None = None,
                 contexto: FonteDeContexto | None = None) -> RespostaOpiniaoAtivo:
    """CTR-IA-01 v1.1: uma chamada por elo da cadeia para os horizontes ainda pendentes.

    O primeiro elo recebe todos os horizontes que tem o que escolher; item ausente ou rejeitado segue
    sozinho para o proximo elo (TASK-IA-26) e, se nenhum responder, cai na regra. Horizonte que so
    permite SEM_BASE nao vai ao modelo. Sem segunda tentativa no mesmo elo (custaria outra chamada).
    """
    cadeia = como_cadeia(provedor)
    pedidos = [pedido.do_horizonte(h) for h in pedido.horizontes]
    ao_modelo = [p for p in pedidos if list(p.permitidas) != [SEM_BASE]]
    trechos: list[TrechoDeContexto] = []
    validos: dict[int, tuple[dict, str]] = {}
    motivos: dict[int, list[str]] = {p.horizonte_pregoes: [] for p in pedidos}
    chamadas: dict[int, int] = {p.horizonte_pregoes: 0 for p in pedidos}

    if cadeia is None:
        for p in ao_modelo:
            motivos[p.horizonte_pregoes].append("sem provedor")
    elif ao_modelo:
        trechos = _trechos_do_ativo(ao_modelo, contexto)
        sistema_do_ativo = (sistema or SISTEMA) + INSTRUCAO_DO_ATIVO
        schema = schema_do_ativo(schema_do_item or SCHEMA_DA_RESPOSTA)
        for elo in cadeia.elos:
            pendentes = [p for p in ao_modelo if p.horizonte_pregoes not in validos]
            if not pendentes:
                break
            for p in pendentes:
                chamadas[p.horizonte_pregoes] += 1
            itens, motivo = None, "sem lista de itens"
            try:
                bruto = cadeia.chamar(elo, pedido.uso, sistema_do_ativo, montar_mensagem_ativo(pendentes, trechos),
                                      schema)
                itens = json.loads(bruto).get("itens")
            except ErroDoProvedor as erro:
                motivo = f"provedor: {erro}"
            except (json.JSONDecodeError, AttributeError):
                motivo = "resposta não é JSON válido"
            if not isinstance(itens, list):
                for p in pendentes:
                    motivos[p.horizonte_pregoes].append(f"{elo.nome}: {motivo}")
                continue
            por_horizonte = {i.get("horizonte_pregoes"): i for i in itens if isinstance(i, dict)}
            for p in pendentes:
                item = por_horizonte.get(p.horizonte_pregoes)
                if item is None:
                    motivos[p.horizonte_pregoes].append(f"{elo.nome}: horizonte ausente na resposta")
                    continue
                valido, erros = validar(item, p, trechos)
                if valido is None:
                    motivos[p.horizonte_pregoes].append(f"{elo.nome}: rejeitada: " + "; ".join(erros))
                else:
                    validos[p.horizonte_pregoes] = (valido, elo.nome)

    saida: list[ItemOpiniaoAtivo] = []
    for p in pedidos:
        h = p.horizonte_pregoes
        if h in validos:
            corpo, quem = validos[h]
            r = _resposta(p, corpo, trechos, quem, skills_versao, ORIGEM_MODELO, chamadas[h])
        else:
            if not motivos[h]:
                motivos[h].append("só SEM_BASE permitido")
            # A linha diz quem respondeu: aqui foi a regra, mesmo que algum modelo tenha sido chamado.
            r = _resposta(p, resposta_de_regra(p), [], MODELO_REGRA, skills_versao, ORIGEM_REGRA, chamadas[h])
        log.info("opiniao simbolo=%s horizonte=%d skills=%s modelo=%s origem=%s chamadas=%d motivo=%s",
                 p.simbolo, h, skills_versao, r.modelo, r.origem, chamadas[h], " | ".join(motivos[h]) or "-")
        saida.append(ItemOpiniaoAtivo(horizonte_pregoes=h, **r.model_dump()))

    gemini = [e for e in (cadeia.elos if cadeia else []) if e.tipo == GEMINI]
    return RespostaOpiniaoAtivo(
        simbolo=pedido.simbolo, data_pregao=pedido.data_pregao,
        modelo=cadeia.nome if cadeia else MODELO_REGRA, skills_versao=skills_versao, itens=saida,
        cota=CotaDaResposta(
            balde=pedido.uso,
            restante_hoje=cadeia.governador.restante(pedido.uso) if gemini else None,
            gemini_disponivel=any(cadeia.governador.disponivel(e.nome, pedido.uso) for e in gemini)))


def opinar(pedido: PedidoOpiniao, provedor: ProvedorLLM | Cadeia | None, skills_versao: str,
           sistema: str | None = None, schema: dict | None = None,
           contexto: FonteDeContexto | None = None, balde: str = "lote") -> RespostaOpiniao:
    """`sistema` e `schema` vem das skills selecionadas (TASK-IA-04); sem skills, o prompt embutido.

    Aceita um provedor solto (vira cadeia de um elo, com a segunda tentativa) ou a cadeia montada.
    """
    cadeia = como_cadeia(provedor)
    origem, tentativas, motivo = ORIGEM_REGRA, 0, ""
    nome_modelo = cadeia.nome if cadeia is not None else MODELO_REGRA
    corpo: dict | None = None
    trechos: list[TrechoDeContexto] = []
    if cadeia is None:
        motivo = "sem provedor"
    elif list(pedido.permitidas) == [SEM_BASE]:
        motivo = "só SEM_BASE permitido"  # nada a escolher: dispensa a chamada
    else:
        trechos = limitar(contexto.trechos(pedido)) if contexto is not None else []
        corpo, tentativas, motivo, quem = _consultar(cadeia, balde, pedido, sistema or SISTEMA,
                                                     schema or SCHEMA_DA_RESPOSTA, trechos)
        if corpo is not None:
            origem, nome_modelo = ORIGEM_MODELO, quem
    if corpo is None:
        corpo = resposta_de_regra(pedido)
    log.info("opiniao simbolo=%s horizonte=%d skills=%s modelo=%s origem=%s tentativas=%d motivo=%s",
             pedido.simbolo, pedido.horizonte_pregoes, skills_versao, nome_modelo, origem, tentativas,
             motivo or "-")
    return _resposta(pedido, corpo, trechos if origem == ORIGEM_MODELO else [], nome_modelo, skills_versao,
                     origem, tentativas)