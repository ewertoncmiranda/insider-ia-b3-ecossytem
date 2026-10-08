"""python -m app.fichas --tipo {evidencia,setores,ativos,mercado,todas} [--ate-ano AAAA] [--saida DIR]"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from datetime import date
from pathlib import Path

TIPOS = ("evidencia", "setores", "ativos", "mercado")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.fichas", description="Fichas de anos fechados (SPEC 6.3)")
    parser.add_argument("--tipo", choices=(*TIPOS, "todas"), default="todas")
    parser.add_argument("--ate-ano", type=int, default=date.today().year - 1,
                        help="ultimo ano fechado (padrao: ano passado; o corrente nunca entra)")
    parser.add_argument("--saida", type=Path,
                        default=Path(os.getenv("DIR_CONHECIMENTO", Path(__file__).resolve().parents[2] / "conhecimento")))
    argumentos = parser.parse_args(argv)
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s fichas - %(message)s")
    log = logging.getLogger("fichas")

    if argumentos.ate_ano >= date.today().year:
        log.error("ano %s nao esta fechado: o ano corrente nunca entra em ficha (SPEC 6.4)", argumentos.ate_ano)
        return 2

    from app.fichas import ativos, banco, contexto, evidencia, ficha, mercado, setores

    inicio = time.monotonic()
    conexao = banco.conectar()
    try:
        base = banco.carregar(conexao, date(argumentos.ate_ano, 12, 31))
    finally:
        conexao.close()
    log.info("carga: %s papeis com preco, %s no universo das fichas (%.0fs)",
             len(base.precos), len(base.universo), time.monotonic() - inicio)
    ctx = contexto.montar(base)

    construtores = {
        "evidencia": lambda: evidencia.montar_todas(ctx),
        "setores": lambda: setores.montar_todas(ctx),
        "ativos": lambda: [f for f in (ativos.montar(ctx, s) for s in base.universo) if f],
        "mercado": lambda: mercado.montar_todas(ctx),
    }
    tipos = TIPOS if argumentos.tipo == "todas" else (argumentos.tipo,)
    hoje = date.today()
    totais = {"gravadas": 0, "inalteradas": 0}
    for tipo in tipos:
        fichas = construtores[tipo]()
        gravadas = sum(ficha.gravar(f, argumentos.saida, hoje) for f in fichas)
        totais["gravadas"] += gravadas
        totais["inalteradas"] += len(fichas) - gravadas
        maior = max((len(f.texto(hoje).encode("utf-8")) for f in fichas), default=0)
        log.info("%s: %s fichas, %s gravadas (hash novo), maior %s bytes", tipo, len(fichas), gravadas, maior)
    log.info("Fichas concluidas | tipos=%s | gravadas=%s | inalteradas=%s | ate=%s | %.0fs",
             ",".join(tipos), totais["gravadas"], totais["inalteradas"], argumentos.ate_ano, time.monotonic() - inicio)
    return 0


if __name__ == "__main__":
    sys.exit(main())
