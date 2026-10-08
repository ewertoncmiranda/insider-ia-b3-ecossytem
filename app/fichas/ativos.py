"""Ficha de ativo (TASK-IA-08, SPEC 6.3): um papel liquido com DFP anual.

Universo: papeis com fator LIQUIDEZ_63D e ao menos um balanco anual - o
"~300" do SPEC e teto, nao meta. So anos fechados; ate 4 KB por ficha.
"""

from __future__ import annotations

import bisect
from collections import defaultdict
from datetime import date

from app.fichas import precos
from app.fichas.contexto import Contexto
from app.fichas.ficha import LIMITE_ATIVO_BYTES, Ficha, num, pct, pct_sem_sinal, tabela

FONTES = ["cotacao_b3_diaria", "indicador_fundamentalista", "provento_contabil", "evento_corporativo", "fator_valor"]
PREGOES_REACAO = 5


def montar(ctx: Contexto, simbolo: str) -> Ficha | None:
    base = ctx.base
    serie_bruta = base.precos.get(simbolo, [])
    retornos = ctx.retornos.get(simbolo, {})
    if len(serie_bruta) < 2 or not retornos:
        return None
    _, nome, setor = base.empresa.get(simbolo, (None, None, None))
    grupo = ctx.grupo(simbolo)
    balancos = {b.ano: b for b in base.balancos.get(simbolo, [])}
    proventos = base.proventos_por_acao.get(simbolo, {})
    por_ano = precos.por_ano(retornos)
    anos = sorted(a for a in por_ano if a <= base.ate.year)
    primeiro, ultimo = anos[0], anos[-1]

    entregas = [b.data_entrega for b in balancos.values() if b.data_entrega]
    entregas += [e for _, e in proventos.values() if e]
    disponivel_ate = max([serie_bruta[-1][0], *entregas])

    linhas = []
    for ano in anos:
        retorno = precos.composto(por_ano[ano])
        merc = ctx.mercado_por_ano.get(ano)
        fim = precos.fechamento_ate(serie_bruta, date(ano, 12, 31))
        b = balancos.get(ano)
        pl = None
        if b and b.lpa and fim:
            pl = fim[1] / b.lpa
        dy = None
        if ano in proventos and fim and fim[1] > 0:
            dy = proventos[ano][0] / fim[1]
        seguinte = precos.composto(por_ano[ano + 1]) if ano + 1 in por_ano and ano + 1 <= base.ate.year else None
        # Quando a linha inteira ficou publica (ponto no tempo, SPEC 6.4): fim do
        # ano, entrega da DFP e dos proventos do ano. O RAG filtra por esta data.
        disponivel = max([date(ano, 12, 31)] + [d for d in (
            b.data_entrega if b else None, proventos.get(ano, (None, None))[1]) if d])
        linhas.append([
            str(ano), f"{disponivel:%d/%m/%y}", pct(retorno), pct(None if retorno is None or merc is None else retorno - merc),
            pct_sem_sinal(precos.volatilidade(por_ano[ano]), 0), pct(precos.drawdown_maximo(por_ano[ano]), 0),
            "neg." if pl is not None and pl < 0 else num(pl), num(b.roe if b else None),
            num(b.margem if b else None), pct_sem_sinal(dy), pct(seguinte),
        ])

    acumulado = precos.composto([retornos[d] for d in sorted(retornos)])
    merc_periodo = precos.composto([ctx.mercado[d] for d in sorted(ctx.mercado) if d >= min(retornos)])
    beta, n_beta = precos.beta(retornos, ctx.mercado)
    queda = precos.pior_queda(retornos)
    pls = [float(l[6].replace(",", ".")) for l in linhas if l[6] not in ("—", "neg.")]
    roes = [b.roe for b in balancos.values() if b.roe is not None]

    resumo = [
        f"{simbolo} — {nome or 'empresa sem nome no FCA'}; setor {setor or '—'} (grupo {grupo or '—'}).",
        f"{primeiro}–{ultimo}: retorno acumulado {pct(acumulado, 0)} contra {pct(merc_periodo, 0)} da média "
        f"igual-peso dos papéis líquidos; beta {num(beta, 2)} (n={n_beta} pregões).",
    ]
    if queda:
        recuperou = (f"recuperada em {queda['pregoes_recuperacao']} pregões ({queda['recuperou']:%m/%Y})"
                     if queda.get("recuperou") else "não recuperada até o fim de " + str(ultimo))
        resumo.append(f"Pior queda: {pct(queda['queda'], 0)} de {queda['pico']:%m/%Y} a {queda['vale']:%m/%Y}, {recuperou}.")
    mp = precos.quantis(pls, (0.5,))[0]
    mr = precos.quantis(roes, (0.5,))[0]
    resumo.append(f"Medianas no período: P/L {num(mp)} (anos com lucro, n={len(pls)}), ROE {num(mr)}% (n={len(roes)}).")

    eventos = base.eventos.get(simbolo, [])
    texto_eventos = "\n".join(
        f"- {d:%d/%m/%Y}: {tipo.lower()} (fator de ações {num(fa, 4)}; preços anteriores ajustados)"
        for d, _, tipo, fa in eventos
    ) or "- Nenhum desdobramento, grupamento ou bonificação inferido com confiança ≥ 0,8."

    padroes = _padroes(ctx, simbolo, retornos, balancos, primeiro, ultimo)

    sem_dfp = [str(a) for a in anos if a not in balancos]
    saltos = ctx.saltos.get(simbolo, [])
    limitacoes = [
        f"Eventos corporativos inferidos no banco: {base.eventos_total} registros no total; só eventos com "
        "confiança ≥ 0,8 ajustam o preço. Desdobramento sem marca ex no COTAHIST não é ajustado.",
        f"Primeiro ano ({primeiro}) começa no primeiro pregão disponível, não em janeiro, se o papel estreou no ano.",
        "P/L e DY usam o fechamento bruto de 31/12; o LPA do exercício só fica público na entrega da DFP "
        f"(ano seguinte). DY vem da DVA por período contábil, não por data-com.",
    ]
    if sem_dfp:
        limitacoes.append(f"Anos sem DFP anual: {', '.join(sem_dfp)} (P/L, ROE e margem ausentes, não zero).")
    if saltos:
        limitacoes.append(f"{len(saltos)} variação(ões) diária(s) acima de 40% sem evento inferido foram "
                          f"excluídas das estatísticas ({', '.join(f'{d:%d/%m/%Y}' for d in saltos[:3])}"
                          f"{'…' if len(saltos) > 3 else ''}).")
    limitacoes.append(f"Ano corrente fora da ficha; dados até {base.ate:%d/%m/%Y}.")

    cabecalho = {
        "tipo": "ativo", "simbolo": simbolo, "setor": setor or "", "grupo_setor": grupo or "",
        "cobertura": f"{primeiro}-{ultimo}", "disponivel_ate": disponivel_ate, "fonte": FONTES,
    }
    secoes = [
        ("Resumo", "\n".join(resumo)),
        ("Por ano", tabela(["Ano", "Disp.", "Retorno", "vs merc.", "Vol.", "Queda máx.", "P/L fim", "ROE %",
                            "Margem %", "DY", "Ret. ano seg."], linhas)),
        ("Eventos", texto_eventos),
        ("Padrões observados", "\n".join(f"- {p}" for p in padroes) or "- Sem amostra suficiente."),
        ("Limitações", "\n".join(f"- {l}" for l in limitacoes)),
    ]
    ficha = Ficha(f"ativos/{simbolo}.md", cabecalho, secoes)
    return _caber(ficha)


def _padroes(ctx: Contexto, simbolo, retornos, balancos, primeiro, ultimo) -> list[str]:
    saida = []
    # Sazonalidade: retorno medio por mes do calendario, contra o mercado.
    mensal: dict[tuple[int, int], float] = defaultdict(lambda: 1.0)
    mercado_mensal: dict[tuple[int, int], float] = defaultdict(lambda: 1.0)
    for d, r in retornos.items():
        mensal[(d.year, d.month)] *= 1 + r
        if d in ctx.mercado:
            mercado_mensal[(d.year, d.month)] *= 1 + ctx.mercado[d]
    por_mes: dict[int, list[float]] = defaultdict(list)
    for (ano, mes), nivel in mensal.items():
        por_mes[mes].append(nivel - mercado_mensal[(ano, mes)])
    medias = {m: sum(v) / len(v) for m, v in por_mes.items() if len(v) >= 5}
    if len(medias) >= 6:
        melhor = max(medias, key=medias.get)
        pior = min(medias, key=medias.get)
        saida.append(f"Sazonalidade (excesso sobre o mercado por mês, {primeiro}–{ultimo}): melhor mês {melhor:02d} "
                     f"({pct(medias[melhor])}, n={len(por_mes[melhor])} anos), pior {pior:02d} "
                     f"({pct(medias[pior])}, n={len(por_mes[pior])}); diferença pequena perto do ruído mensal.")
    # Reacao a divulgacao da DFP: excesso nos 5 pregoes a partir da entrega.
    dias = sorted(retornos)
    reacoes = []
    for b in balancos.values():
        if not b.data_entrega or b.data_entrega > ctx.base.ate:
            continue
        i = bisect.bisect_left(dias, b.data_entrega)
        janela = dias[i:i + PREGOES_REACAO]
        if len(janela) == PREGOES_REACAO:
            ativo = precos.composto([retornos[d] for d in janela])
            merc = precos.composto([ctx.mercado.get(d, 0.0) for d in janela])
            reacoes.append(ativo - merc)
    if len(reacoes) >= 4:
        positivos = sum(1 for r in reacoes if r > 0)
        saida.append(f"Reação à DFP (excesso em {PREGOES_REACAO} pregões após a entrega): média "
                     f"{pct(sum(reacoes) / len(reacoes))}, positiva em {positivos} de {len(reacoes)} divulgações.")
    return saida


def _caber(ficha: Ficha) -> Ficha:
    """Ate 4 KB (SPEC 6.3): corta primeiro os padroes, depois os anos mais antigos."""
    from datetime import date as _d

    def tamanho() -> int:
        return len(ficha.texto(_d(2000, 1, 1)).encode("utf-8"))

    if tamanho() > LIMITE_ATIVO_BYTES:
        ficha.secoes = [(t, c) for t, c in ficha.secoes if t != "Padrões observados"]
    while tamanho() > LIMITE_ATIVO_BYTES:
        titulo, corpo = next((t, c) for t, c in ficha.secoes if t == "Por ano")
        linhas = corpo.split("\n")
        if len(linhas) <= 4:
            break
        del linhas[2]  # remove o ano mais antigo (depois do cabecalho e do separador)
        ficha.secoes = [(t, "\n".join(linhas) if t == "Por ano" else c) for t, c in ficha.secoes]
    return ficha
