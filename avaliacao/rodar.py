"""Avaliacao offline (NFR-IA-05): roda o conjunto fixo de dossies e imprime as metricas.

    python -m avaliacao.rodar [--provedor regra|gemini] [--limite N]

`regra` (padrao) nao usa modelo: confere que a reserva por regra reproduz `esperado/` byte a byte e
que todo esperado passa no validador. `gemini` pergunta a cadeia de modelos Gemini (GEMINI_API_KEY,
GEMINI_MODELOS; gasta cota do balde `lote`) e mede formato valido, taxa de reserva por regra e citacoes invalidas. Sai com codigo 1 se `regra` divergir.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app import skills as skills_mod
from app.config import Settings
from app.modelos import PedidoOpiniao
from app.orquestrador import opinar
from app.provedores.cadeia import montar_cadeia
from app.regras import resposta_de_regra
from app.validador import validar

RAIZ = Path(__file__).resolve().parent


def carregar(data: str | None = None) -> list[tuple[PedidoOpiniao, dict]]:
    """Pares (pedido, esperado) de todos os dias em avaliacao/dossies (ou so de `data`)."""
    pares: list[tuple[PedidoOpiniao, dict]] = []
    for arquivo in sorted((RAIZ / "dossies").glob("*.jsonl")):
        if data and arquivo.stem != data:
            continue
        esperado_arquivo = RAIZ / "esperado" / arquivo.name
        pedidos = [json.loads(linha) for linha in arquivo.read_text(encoding="utf-8").splitlines() if linha]
        esperados = [json.loads(linha) for linha in esperado_arquivo.read_text(encoding="utf-8").splitlines()
                     if linha]
        assert len(pedidos) == len(esperados), f"{arquivo.name}: dossies e esperado de tamanhos diferentes"
        pares += [(PedidoOpiniao(**p), e) for p, e in zip(pedidos, esperados, strict=True)]
    return pares


def sem_chaves_de_identificacao(esperado: dict) -> dict:
    return {k: v for k, v in esperado.items() if k not in ("simbolo", "horizonte_pregoes")}


def rodar(provedor: str, limite: int | None = None, com_skills: bool = True) -> dict:
    pares = carregar()
    if provedor == "gemini":
        # So conta dossie em que ha o que escolher: SEM_BASE forcado nunca chama o modelo.
        pares = [(p, e) for p, e in pares if list(p.permitidas) != ["SEM_BASE"]]
    pares = pares[:limite]
    metricas = {"total": len(pares), "divergentes_da_regra": 0, "invalidos_no_validador": 0,
                "reserva_por_regra": 0, "citacoes_invalidas": 0, "formato_ok": 0}
    cadeia = None
    cfg = Settings.do_ambiente()
    conjunto = skills_mod.listar(cfg.dir_skills) if com_skills else []
    versao = skills_mod.versao_do_conjunto(conjunto)
    if provedor == "gemini":
        cadeia = montar_cadeia(cfg, "lote")
        if cadeia is None:
            raise SystemExit("Gemini nao configurado (GEMINI_API_KEY/GEMINI_MODELOS)")
    for pedido, esperado in pares:
        if provedor == "regra":
            if resposta_de_regra(pedido) != sem_chaves_de_identificacao(esperado):
                metricas["divergentes_da_regra"] += 1
            sem_invalida = {**sem_chaves_de_identificacao(esperado), "o_que_invalida": []}
            if validar(sem_invalida, pedido)[0] is None:
                metricas["invalidos_no_validador"] += 1
            metricas["formato_ok"] += 1
        else:
            escolhidas = skills_mod.selecionar(conjunto, pedido.horizonte_pregoes, [e.id for e in pedido.evidencias])
            resposta = opinar(pedido, cadeia, versao, sistema=skills_mod.montar_sistema(escolhidas) or None,
                              schema=skills_mod.schema_da_resposta(cfg.dir_skills) if conjunto else None)
            metricas["formato_ok"] += 1
            if resposta.origem == "REGRA":
                metricas["reserva_por_regra"] += 1
            ids = {e.id for e in pedido.evidencias}
            metricas["citacoes_invalidas"] += sum(1 for j in resposta.justificativa if j.evidencia_id not in ids)
    return metricas


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Avaliacao offline do servico de IA")
    parser.add_argument("--provedor", choices=["regra", "gemini"], default="regra")
    parser.add_argument("--limite", type=int)
    parser.add_argument("--sem-skills", action="store_true", help="usa o prompt embutido (linha de base)")
    argumentos = parser.parse_args(argv)
    metricas = rodar(argumentos.provedor, argumentos.limite, not argumentos.sem_skills)
    print(json.dumps(metricas, ensure_ascii=False, indent=2))
    ruim = metricas["divergentes_da_regra"] or metricas["invalidos_no_validador"]
    return 1 if argumentos.provedor == "regra" and ruim else 0


if __name__ == "__main__":
    sys.exit(main())
