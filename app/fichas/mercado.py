"""Fichas de mercado (TASK-IA-08, SPEC 6.3): uma por ano fechado e
`regimes.md`. "Mercado" = media igual-peso dos papeis liquidos das fichas
(nao o Ibovespa, que nao esta no banco). Puro.
"""

from __future__ import annotations

from datetime import date

from app.fichas import precos
from app.fichas.contexto import Contexto
from app.fichas.ficha import Ficha, num, pct, pct_sem_sinal, tabela

FONTES = ["cotacao_b3_diaria", "evento_corporativo", "indice_macro", "fator_mercado_mensal"]

# Regimes descritos no SPEC 6.3. Janelas fixas, escritas antes de olhar o
# resultado; o numero sai do dado.
REGIMES = (
    ("Recessão 2015–16", date(2015, 1, 1), date(2016, 12, 31), "PIB caiu dois anos seguidos; Selic chegou a 14,25%."),
    ("Rali eleitoral 2018", date(2018, 8, 1), date(2018, 10, 31), "Agosto a outubro de ano de eleição presidencial."),
    ("Covid: queda", date(2020, 2, 20), date(2020, 3, 23), "Do pico de fevereiro ao fundo de março de 2020."),
    ("Covid: recuperação", date(2020, 3, 24), date(2020, 12, 31), "Do fundo de março ao fim de 2020."),
    ("Rali eleitoral 2022", date(2022, 8, 1), date(2022, 10, 31), "Agosto a outubro de ano de eleição presidencial."),
    ("Juros altos 2022–24", date(2022, 1, 1), date(2024, 12, 31), "Selic em dois dígitos na maior parte do período."),
)


# Mes de fator long-short acima de 100% em modulo e evento corporativo nao
# inferido (TELB4 x9.546 em 01/2011, PDGR3 x47 em 10/2015): fora da conta.
LIMITE_FATOR_MENSAL = 1.0


def fator_limpo(serie: list[tuple[date, float]], inicio: date, fim: date) -> tuple[list[float], int]:
    """Retornos mensais do fator na janela, sem os meses suspeitos; e quantos sairam."""
    janela = [r for d, r in serie if inicio <= d <= fim]
    limpos = [r for r in janela if abs(r) <= LIMITE_FATOR_MENSAL]
    return limpos, len(janela) - len(limpos)


def _ultimo_ate(serie: list[tuple[date, float]], dia: date) -> float | None:
    anteriores = [v for d, v in serie if d <= dia]
    return anteriores[-1] if anteriores else None


def macro_do_ano(ctx: Contexto, ano: int) -> dict:
    m = ctx.base.macro
    cdi = [v for d, v in m.get("CDI", []) if d.year == ano]
    ipca = [v for d, v in m.get("IPCA", []) if d.year == ano]
    return {
        "selic_fim": _ultimo_ate([(d, v) for d, v in m.get("SELIC", []) if d.year == ano], date(ano, 12, 31)),
        "cdi": precos.composto([v / 100 for v in cdi]) if len(cdi) > 200 else None,
        "ipca": precos.composto([v / 100 for v in ipca]) if len(ipca) == 12 else None,
    }


def retornos_do_ano(ctx: Contexto, ano: int) -> dict[str, float]:
    saida = {}
    for simbolo, rs in ctx.retornos.items():
        do_ano = [r for d, r in sorted(rs.items()) if d.year == ano]
        if len(do_ano) > 200:
            saida[simbolo] = precos.composto(do_ano)
    return saida


def montar_ano(ctx: Contexto, ano: int) -> Ficha | None:
    diarios = [ctx.mercado[d] for d in sorted(ctx.mercado) if d.year == ano]
    if len(diarios) < 200:
        return None
    rets = retornos_do_ano(ctx, ano)
    if len(rets) < 10:
        return None
    ordenados = sorted(rets, key=lambda s: (rets[s], s))
    mediana = precos.quantis(list(rets.values()), (0.5,))[0]
    altas = sum(1 for r in rets.values() if r > 0) / len(rets)
    macro = macro_do_ano(ctx, ano)
    fatores, descartados = [], 0
    for codigo, serie in sorted(ctx.base.fator_mercado.items()):
        do_ano, fora = fator_limpo(serie, date(ano, 1, 1), date(ano, 12, 31))
        descartados += fora
        if len(do_ano) >= 10:
            fatores.append(f"{codigo} {pct(precos.composto(do_ano))}")

    linhas = [
        ["Retorno médio igual-peso", pct(ctx.mercado_por_ano.get(ano))],
        ["Retorno mediano dos papéis", pct(mediana)],
        ["Papéis em alta no ano", f"{pct_sem_sinal(altas, 0)} de {len(rets)}"],
        ["Volatilidade do mercado", pct_sem_sinal(precos.volatilidade(diarios), 0)],
        ["Queda máxima no ano", pct(precos.drawdown_maximo(diarios), 0)],
        ["Selic meta no fim do ano", "—" if macro["selic_fim"] is None else f"{num(macro['selic_fim'], 2)}%"],
        ["CDI no ano", pct_sem_sinal(macro["cdi"])],
        ["IPCA no ano", pct_sem_sinal(macro["ipca"])],
    ]
    maiores = ", ".join(f"{s} {pct(rets[s], 0)}" for s in reversed(ordenados[-5:]))
    menores = ", ".join(f"{s} {pct(rets[s], 0)}" for s in ordenados[:5])
    limitacoes = ["- Mercado = média igual-peso dos papéis líquidos (não é o Ibovespa, ausente do banco).",
                  "- Só papéis com o ano (quase) inteiro de pregões; variação diária acima de 40% sem evento inferido "
                  "fica fora."]
    if descartados:
        limitacoes.append(f"- {descartados} mês(es) de fator long-short acima de 100% em módulo ficaram fora "
                          "(evento corporativo não inferido distorce a carteira).")
    if macro["cdi"] is None or macro["ipca"] is None:
        limitacoes.append("- CDI, Selic e IPCA só existem no banco a partir de 2016.")
    cabecalho = {"tipo": "mercado", "ano": ano, "papeis": len(rets), "disponivel_ate": date(ano, 12, 31),
                 "fonte": FONTES}
    secoes = [
        ("Resumo", f"{ano}: papéis líquidos renderam {pct(ctx.mercado_por_ano.get(ano))} em média igual-peso "
                   f"(mediana {pct(mediana)}); {pct_sem_sinal(altas, 0)} subiram no ano. CDI "
                   f"{pct_sem_sinal(macro['cdi'])}, IPCA {pct_sem_sinal(macro['ipca'])}."),
        ("Números do ano", tabela(["Medida", "Valor"], linhas)),
        ("Maiores e menores", f"- Maiores: {maiores}\n- Menores: {menores}"),
        ("Fatores de referência", ("Retorno no ano das carteiras long-short (fator_mercado_mensal): "
                                   + "; ".join(fatores) + ".") if fatores else "Sem fatores de referência no ano."),
        ("Limitações", "\n".join(limitacoes)),
    ]
    return Ficha(f"mercado/{ano}.md", cabecalho, secoes)


def montar_regimes(ctx: Contexto) -> Ficha:
    linhas, descartados = [], 0
    for nome, inicio, fim, descricao in REGIMES:
        if fim > ctx.base.ate:
            continue
        dias = [d for d in sorted(ctx.mercado) if inicio <= d <= fim]
        if len(dias) < 10:
            continue
        diarios = [ctx.mercado[d] for d in dias]
        selic = _ultimo_ate(ctx.base.macro.get("SELIC", []), fim)
        wml, fora_w = fator_limpo(ctx.base.fator_mercado.get("WML", []), inicio, fim)
        hml, fora_h = fator_limpo(ctx.base.fator_mercado.get("HML", []), inicio, fim)
        descartados += fora_w + fora_h
        linhas.append([nome, f"{inicio:%m/%Y}–{fim:%m/%Y}", str(len(dias)), pct(precos.composto(diarios)),
                       pct(precos.drawdown_maximo(diarios), 0), pct_sem_sinal(precos.volatilidade(diarios), 0),
                       "—" if selic is None else f"{num(selic, 2)}%",
                       pct(precos.composto(wml)) if len(wml) >= 2 else "—",
                       pct(precos.composto(hml)) if len(hml) >= 2 else "—"])
    descricoes = "\n".join(f"- **{n}**: {d}" for n, _, f, d in REGIMES if f <= ctx.base.ate)
    cabecalho = {"tipo": "mercado", "documento": "regimes", "disponivel_ate": ctx.base.ate, "fonte": FONTES}
    secoes = [
        ("Resumo", "Episódios de mercado com janelas fixas (definidas antes de olhar o resultado) e como a média "
                   "igual-peso dos papéis líquidos e os fatores momentum (WML) e valor (HML) se comportaram."),
        ("Regimes", tabela(["Regime", "Janela", "Pregões", "Mercado", "Queda máx.", "Vol.", "Selic fim",
                            "WML", "HML"], linhas)),
        ("Definições", descricoes),
        ("Limitações", "- Janelas de calendário, não detectadas pelos dados; regime futuro não precisa repetir.\n"
                       "- Selic só a partir de 2016; WML/HML desde 2010 (fator_mercado_mensal).\n"
                       "- Rali eleitoral de 2026 fica fora (ano corrente)."
                       + (f"\n- {descartados} mês(es) de WML/HML acima de 100% em módulo ficaram fora (evento "
                          "corporativo não inferido)." if descartados else "")),
    ]
    return Ficha("mercado/regimes.md", cabecalho, secoes)


def montar_todas(ctx: Contexto) -> list[Ficha]:
    anos = sorted({d.year for d in ctx.mercado if d.year <= ctx.base.ate.year})
    fichas = [montar_ano(ctx, ano) for ano in anos]
    return [f for f in fichas if f] + [montar_regimes(ctx)]
