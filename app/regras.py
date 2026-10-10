"""Reserva por regra (REQ-IA-04): a opiniao que existe sem modelo, montada so dos numeros da entrada.

Usada quando nao ha o que escolher (so SEM_BASE permitido), quando o Gemini esta indisponivel (sem chave, cota ou erro) ou
quando a resposta do modelo e rejeitada duas vezes. `condicoes_contrarias` tambem preenche
`o_que_invalida` das respostas do modelo: esse campo nunca e escrito por ele.
"""

from __future__ import annotations

from app.modelos import NEGATIVO, POSITIVO, PedidoOpiniao

MAXIMO_DE_JUSTIFICATIVAS = 5
MAXIMO_DE_CONDICOES = 3


def condicoes_contrarias(pedido: PedidoOpiniao, opiniao: str) -> list[str]:
    """"O que invalida" = evidencias que apontam no sentido contrario da opiniao (ate 3)."""
    sentido = {POSITIVO: 1, NEGATIVO: -1}.get(opiniao)
    if sentido is None:
        return []
    contra = [e for e in pedido.evidencias if e.direcao == -sentido]
    return [f"Há evidência em sentido contrário: {e.rotulo.lower()} ({e.valor})."
            for e in contra[:MAXIMO_DE_CONDICOES]]


def resposta_de_regra(pedido: PedidoOpiniao) -> dict:
    """{opiniao, risco, justificativa, o_que_invalida} pela regra; a ordem de `permitidas` vai da
    opiniao mais forte para a mais cautelosa, entao a primeira e a da regra."""
    opiniao = pedido.permitidas[0]
    sentido = {POSITIVO: 1, NEGATIVO: -1}.get(opiniao)
    direcionais = [e for e in pedido.evidencias if e.direcao != 0]
    # A justificativa lista o que SUSTENTA a opiniao; o que a contraria vira "o que invalida".
    a_favor = [e for e in direcionais if e.direcao == sentido] if sentido is not None else direcionais
    if not a_favor:
        a_favor = pedido.evidencias[:2]
    justificativa = [{"evidencia_id": e.id, "leitura": f"{e.rotulo}: {e.valor}."}
                     for e in a_favor[:MAXIMO_DE_JUSTIFICATIVAS]]
    return {"opiniao": opiniao, "risco": pedido.risco_calculado, "justificativa": justificativa,
            "o_que_invalida": condicoes_contrarias(pedido, opiniao)}
