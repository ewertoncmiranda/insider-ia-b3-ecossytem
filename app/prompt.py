"""Prompt e schema de saida (portados do gerar-insights, versao 1.2). TASK-IA-04 os converte em skills."""

from __future__ import annotations

import json

from app.contexto import TrechoDeContexto
from app.modelos import OPINIOES, RISCOS, PedidoOpiniao

NOME_DO_HORIZONTE = {21: "curto (cerca de 1 mês, 21 pregões)",
                     63: "médio (cerca de 3 meses, 63 pregões)",
                     126: "longo (cerca de 6 meses, 126 pregões)"}

MAXIMO_DE_EVIDENCIAS_NO_PEDIDO = 8

SCHEMA_DA_RESPOSTA = {
    "type": "object",
    "properties": {
        "opiniao": {"type": "string", "enum": list(OPINIOES)},
        "risco": {"type": "string", "enum": list(RISCOS)},
        "justificativa": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"evidencia_id": {"type": "string"}, "trecho_id": {"type": "string"},
                               "leitura": {"type": "string"}},
                "required": ["leitura"],
            },
        },
    },
    "required": ["opiniao", "risco", "justificativa"],
}

SISTEMA = (
    "Você descreve, em português do Brasil, o que os números de um ativo da B3 indicam para um "
    "horizonte de tempo. Você NÃO é consultor e NÃO recomenda investimento.\n"
    "Regras obrigatórias:\n"
    "1. Use somente as evidências recebidas. Não use conhecimento próprio, notícias nem preços de memória.\n"
    "2. Escolha 'opiniao' somente entre as 'permitidas'. Na dúvida, prefira SINAL_NEUTRO ou SEM_BASE.\n"
    "3. Copie 'risco' exatamente como 'risco_calculado'.\n"
    "4. Use de 2 a 5 itens em 'justificativa', os que mais sustentam a 'opiniao'. Cada item cita um "
    "'evidencia_id' recebido e explica, em UMA frase de até 20 palavras, o que ele indica. Descreva o "
    "dado; não aconselhe nem diga se algo é bom para investir. Não invente números: use só os que "
    "aparecem nas evidências.\n"
    "5. Nunca prometa resultado. Palavras como 'garantido', 'certeza' e 'sem risco' são proibidas."
)


def schema_do_ativo(schema_do_item: dict) -> dict:
    """CTR-IA-01 v1.1: a resposta e `itens[]`, cada um com `horizonte_pregoes` + o schema de um horizonte."""
    item = json.loads(json.dumps(schema_do_item))
    item.setdefault("properties", {})["horizonte_pregoes"] = {"type": "integer"}
    item["required"] = ["horizonte_pregoes", *[c for c in item.get("required", []) if c != "horizonte_pregoes"]]
    return {"type": "object", "properties": {"itens": {"type": "array", "items": item}}, "required": ["itens"]}


INSTRUCAO_DO_ATIVO = (
    "\n\nVocê recebe VÁRIOS horizontes do mesmo ativo. Responda um objeto {\"itens\": [...]} com UM item "
    "por horizonte recebido, cada um com 'horizonte_pregoes' igual ao do pedido. Aplique as regras "
    "acima a cada horizonte separadamente: 'permitidas', 'risco_calculado' e 'evidencias' são as daquele "
    "horizonte."
)


def montar_mensagem_ativo(pedidos: list[PedidoOpiniao], trechos: list[TrechoDeContexto] | None = None) -> str:
    """Mensagem v1.1: um bloco por horizonte (mesmo recorte da v1.0) e os trechos uma vez so."""
    blocos = []
    for pedido in pedidos:
        bloco = json.loads(montar_mensagem(pedido))
        bloco.pop("ativo", None)
        bloco["horizonte_pregoes"] = pedido.horizonte_pregoes
        blocos.append(bloco)
    corpo = {"ativo": pedidos[0].simbolo if pedidos else "", "horizontes": blocos}
    if trechos:
        corpo["trechos"] = [{"trecho_id": t.trecho_id, "texto": t.texto} for t in trechos]
    return json.dumps(corpo, ensure_ascii=False)


def montar_mensagem(pedido: PedidoOpiniao, trechos: list[TrechoDeContexto] | None = None) -> str:
    """Mensagem do usuario: so dados do pedido, em JSON fechado; direcionais primeiro, no maximo 8."""
    ordenadas = sorted(pedido.evidencias, key=lambda e: (e.direcao == 0, e.id))
    corpo = {
        "ativo": pedido.simbolo,
        "horizonte": NOME_DO_HORIZONTE.get(pedido.horizonte_pregoes, f"{pedido.horizonte_pregoes} pregões"),
        "permitidas": list(pedido.permitidas),
        "risco_calculado": pedido.risco_calculado,
        "evidencias": [
            {"evidencia_id": e.id, "o_que_e": e.rotulo, "valor": e.valor,
             "leitura_numerica": {1: "favorável", -1: "desfavorável", 0: "informativa"}[e.direcao]}
            for e in ordenadas[:MAXIMO_DE_EVIDENCIAS_NO_PEDIDO]
        ],
    }
    if trechos:
        corpo["trechos"] = [{"trecho_id": t.trecho_id, "texto": t.texto} for t in trechos]
    return json.dumps(corpo, ensure_ascii=False)
