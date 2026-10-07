"""Fichas de evidencia (TASK-IA-07, SPEC 6.3): o que os dados dizem de cada
fator e regra, com n, periodo e intervalo de confianca. Puro.

Fator: no primeiro pregao de cada mes, os papeis sao divididos em quintis
pelo valor do fator (sentido da direcao esperada: Q5 = o "melhor"); o spread
e a media do retorno a frente de Q5 menos a de Q1. Janelas sem sobreposicao:
21 pregoes mensal, 63 a cada 3 meses, 126 a cada 6 - senao o IC fica
estreito de mentira. IC 95% pela normal (media +- 1,96 dp/raiz(n)).
"""

from __future__ import annotations

import bisect
import math
from datetime import date

from app.fichas import precos
from app.fichas.contexto import Contexto
from app.fichas.ficha import Ficha, num, pct, pct_sem_sinal, tabela

HORIZONTES = ((21, 1), (63, 3), (126, 6))       # (pregoes, passo em meses)
PERIODOS = ((2010, 2015), (2016, 2019), (2020, 2025))
MINIMO_POR_QUINTIL = 5
FONTES_FATOR = ["fator_valor", "fator_definicao", "cotacao_b3_diaria", "evento_corporativo"]


class Precos:
    """Retorno a frente com indice por papel (bisect sem recriar listas)."""

    def __init__(self, ajustadas: dict[str, precos.Serie]):
        self._datas = {s: [d for d, _ in serie] for s, serie in ajustadas.items()}
        self._valores = {s: [p for _, p in serie] for s, serie in ajustadas.items()}

    def a_frente(self, simbolo: str, dia: date, pregoes: int) -> float | None:
        datas = self._datas.get(simbolo)
        if not datas:
            return None
        i = bisect.bisect_left(datas, dia)
        j = i + pregoes
        if i >= len(datas) or j >= len(datas) or datas[i] - dia > _UMA_SEMANA:
            return None
        inicio, fim = self._valores[simbolo][i], self._valores[simbolo][j]
        r = fim / inicio - 1 if inicio > 0 else None
        # saltos sem evento contaminam a media: fora, como nas fichas de ativo
        return None if r is None or abs(r) > 3 else r

    def para_tras(self, simbolo: str, dia: date, pregoes: int) -> float | None:
        datas = self._datas.get(simbolo)
        if not datas:
            return None
        i = bisect.bisect_left(datas, dia) - 1
        j = i - pregoes
        if j < 0 or i < 0:
            return None
        inicio, fim = self._valores[simbolo][j], self._valores[simbolo][i]
        return fim / inicio - 1 if inicio > 0 else None


_UMA_SEMANA = date(2000, 1, 8) - date(2000, 1, 1)


def estatistica(amostra: list[float]) -> dict | None:
    n = len(amostra)
    if n < 3:
        return None
    media = sum(amostra) / n
    dp = math.sqrt(sum((x - media) ** 2 for x in amostra) / (n - 1))
    erro = 1.96 * dp / math.sqrt(n)
    return {"n": n, "media": media, "ic": (media - erro, media + erro),
            "positivos": sum(1 for x in amostra if x > 0) / n}


def quintis(valores: dict[str, float], direcao: int) -> tuple[list[str], list[str]] | None:
    """(Q1, Q5) no sentido da direcao esperada; None se poucos papeis."""
    if len(valores) < MINIMO_POR_QUINTIL * 5:
        return None
    sinal = -1 if direcao < 0 else 1
    ordenados = sorted(valores, key=lambda s: (sinal * valores[s], s))
    tamanho = len(ordenados) // 5
    return ordenados[:tamanho], ordenados[-tamanho:]


def spreads_do_fator(ctx: Contexto, idx: Precos, codigo: str, direcao: int) -> dict:
    """horizonte -> lista de (data, spread, q5_menos_media)."""
    por_data = ctx.base.fatores.get(codigo, {})
    datas = sorted(por_data)
    saida: dict[int, list[tuple[date, float, float]]] = {}
    for pregoes, passo in HORIZONTES:
        pontos = []
        for k, dia in enumerate(datas):
            if k % passo:
                continue
            q = quintis(por_data[dia], direcao)
            if not q:
                continue
            futuros = {s: idx.a_frente(s, dia, pregoes) for s in por_data[dia]}
            futuros = {s: r for s, r in futuros.items() if r is not None}
            baixo = [futuros[s] for s in q[0] if s in futuros]
            alto = [futuros[s] for s in q[1] if s in futuros]
            if len(baixo) < MINIMO_POR_QUINTIL or len(alto) < MINIMO_POR_QUINTIL:
                continue
            media_alto, media_baixo = sum(alto) / len(alto), sum(baixo) / len(baixo)
            media_todos = sum(futuros.values()) / len(futuros)
            pontos.append((dia, media_alto - media_baixo, media_alto - media_todos))
        saida[pregoes] = pontos
    return saida


def regime_em(ctx: Contexto, dia: date) -> str:
    """ALTA se a media igual-peso subiu nos 252 pregoes anteriores."""
    dias = [d for d in ctx.mercado if d < dia][-precos.PREGOES_ANO:]
    if len(dias) < precos.PREGOES_ANO // 2:
        return "SEM_DADO"
    return "ALTA" if precos.composto([ctx.mercado[d] for d in dias]) > 0 else "BAIXA"


def montar_fator(ctx: Contexto, idx: Precos, codigo: str) -> Ficha | None:
    familia, direcao, descricao = ctx.base.fator_definicao.get(codigo, ("?", 0, codigo))
    spreads = spreads_do_fator(ctx, idx, codigo, direcao)
    if not any(spreads.values()):
        return None
    datas = sorted(ctx.base.fatores.get(codigo, {}))
    linhas = []
    regimes = []
    for pregoes, _ in HORIZONTES:
        pontos = spreads.get(pregoes, [])
        recortes = [("Todos", pontos)] + [
            (f"{a}–{b}", [p for p in pontos if a <= p[0].year <= b]) for a, b in PERIODOS]
        for rotulo, recorte in recortes:
            e = estatistica([s for _, s, _ in recorte])
            if e is None:
                continue
            bate = sum(1 for _, _, x in recorte if x > 0) / len(recorte)
            linhas.append([f"{pregoes}", rotulo, str(e["n"]), pct(e["media"]),
                           f"{pct(e['ic'][0])} a {pct(e['ic'][1])}", pct_sem_sinal(e["positivos"], 0),
                           pct_sem_sinal(bate, 0)])
        if pregoes == 21:
            for regime in ("ALTA", "BAIXA"):
                e = estatistica([s for d, s, _ in pontos if regime_em(ctx, d) == regime])
                if e:
                    regimes.append(f"- Mercado em {regime.lower()} nos 12 meses anteriores: spread médio "
                                   f"{pct(e['media'])} em 21 pregões (IC {pct(e['ic'][0])} a {pct(e['ic'][1])}, n={e['n']}).")

    todos21 = estatistica([s for _, s, _ in spreads.get(21, [])])
    sentido = {1: "maior é melhor", -1: "menor é melhor", 0: "sem direção esperada (Q5 = maior valor)"}[direcao]
    if todos21:
        distingue = todos21["ic"][0] > 0 or todos21["ic"][1] < 0
        leitura = ("o IC de 95% não inclui zero" if distingue else
                   "o IC de 95% inclui zero: sem vantagem distinguível do acaso")
        resumo = (f"{descricao} ({familia}; {sentido}). Em 21 pregões, Q5 − Q1 rendeu em média {pct(todos21['media'])} "
                  f"por mês ({datas[0]:%m/%Y}–{datas[-1]:%m/%Y}, n={todos21['n']}); {leitura}.")
    else:
        resumo = f"{descricao} ({familia}; {sentido}). Amostra insuficiente em 21 pregões."

    fim_amostra = max((d for pontos in spreads.values() for d, _, _ in pontos), default=datas[-1])
    cabecalho = {"tipo": "evidencia", "evidencia": f"fator/{codigo}", "familia": familia,
                 "direcao_esperada": direcao, "cobertura": f"{datas[0].year}-{ctx.base.ate.year}",
                 "disponivel_ate": ctx.base.ate, "fonte": FONTES_FATOR}
    secoes = [
        ("Resumo", resumo),
        ("Resultado", "Spread = retorno médio do quintil 5 menos o do quintil 1; \"Q5 > média\" = fração das "
                      "datas em que o quintil 5 superou a média do universo.\n\n"
                      + tabela(["Pregões", "Período", "n", "Spread médio", "IC 95%", "Spread > 0", "Q5 > média"], linhas)),
        ("Por regime", "\n".join(regimes) or "- Amostra insuficiente."),
        ("Limitações", "\n".join([
            f"- Referência mensal (primeiro pregão do mês), última janela encerrada até {fim_amostra:%d/%m/%Y}; "
            "nada do ano corrente.",
            "- Universo: papéis com o fator calculado no mês (líquidos); quintil com menos de 5 papéis é descartado.",
            "- Retorno a frente sobre preço ajustado por evento corporativo inferido (confiança ≥ 0,8); "
            f"{ctx.base.eventos_total} eventos no banco. Retorno acima de 300% na janela é descartado como dado suspeito.",
            "- Sem custo de transação, imposto ou liquidez de execução. Resultado passado não garante o futuro.",
        ])),
    ]
    return Ficha(f"evidencia/fator-{codigo.lower().replace('_', '-')}.md", cabecalho, secoes)


def montar_momentum_semanal(ctx: Contexto, idx: Precos) -> Ficha | None:
    """Teste citado no SPEC (secao 2): quintil de momentum em 20 pregoes contra
    o mercado nos 5 pregoes seguintes, semanal. Refeito aqui sobre o universo
    das fichas, para a ficha carregar n e periodo."""
    universo = set(ctx.base.universo)
    semanas = []
    vistos = set()
    for d in sorted(ctx.mercado):
        chave = d.isocalendar()[:2]
        if chave not in vistos:
            vistos.add(chave)
            semanas.append(d)
    resultado = {"alto": [], "baixo": []}
    for dia in semanas:
        passados = {s: idx.para_tras(s, dia, 20) for s in universo}
        passados = {s: r for s, r in passados.items() if r is not None}
        q = quintis(passados, 1)
        if not q:
            continue
        futuros = {s: idx.a_frente(s, dia, 5) for s in passados}
        futuros = {s: r for s, r in futuros.items() if r is not None}
        if len(futuros) < 25:
            continue
        media = sum(futuros.values()) / len(futuros)
        for nome, grupo in (("baixo", q[0]), ("alto", q[1])):
            rs = [futuros[s] for s in grupo if s in futuros]
            if len(rs) >= MINIMO_POR_QUINTIL:
                resultado[nome].append((dia, sum(rs) / len(rs) - media))
    if not resultado["alto"]:
        return None
    linhas = []
    for nome, rotulo in (("alto", "Maior momentum (Q5)"), ("baixo", "Menor momentum (Q1)")):
        for periodo, filtro in [("Todos", lambda d: True)] + [
                (f"{a}–{b}", (lambda a, b: lambda d: a <= d.year <= b)(a, b)) for a, b in PERIODOS]:
            amostra = [x for d, x in resultado[nome] if filtro(d)]
            e = estatistica(amostra)
            if e:
                linhas.append([rotulo, periodo, str(e["n"]), pct_sem_sinal(e["positivos"]), pct(e["media"], 2),
                               f"{pct(e['ic'][0], 2)} a {pct(e['ic'][1], 2)}"])
    alto = estatistica([x for _, x in resultado["alto"]])
    baixo = estatistica([x for _, x in resultado["baixo"]])
    inicio, fim = resultado["alto"][0][0], resultado["alto"][-1][0]
    resumo = (f"Semanal, {inicio:%m/%Y}–{fim:%m/%Y}: o quintil de maior retorno em 20 pregões bateu a média dos "
              f"papéis líquidos nos 5 pregões seguintes em {pct_sem_sinal(alto['positivos'])} das semanas "
              f"(n={alto['n']}); o de menor, em {pct_sem_sinal(baixo['positivos'])} (n={baixo['n']}). "
              "Perto de 50%: momentum curto não tem vantagem distinguível no histórico.")
    cabecalho = {"tipo": "evidencia", "evidencia": "regra/momentum-20p-semanal",
                 "cobertura": f"{inicio.year}-{fim.year}", "disponivel_ate": ctx.base.ate,
                 "fonte": ["cotacao_b3_diaria", "evento_corporativo"]}
    secoes = [
        ("Resumo", resumo),
        ("Resultado", tabela(["Quintil", "Período", "Semanas", "Bateu a média", "Excesso médio 5p", "IC 95%"], linhas)),
        ("Limitações", "\n".join([
            f"- Universo: os {len(universo)} papéis das fichas de ativo (líquidos e com DFP); o SPEC citava 49,1%/47,2% "
            "num universo mais amplo do COTAHIST 2016–2026 - a diferença de número vem do universo e do período.",
            "- Semanas sobrepõem a janela de 20 pregões passados (não a de 5 à frente).",
            "- Sem custo de transação. Ano corrente fora.",
        ])),
    ]
    return Ficha("evidencia/momentum-20p-semanal.md", cabecalho, secoes)


def montar_regras(ctx: Contexto) -> Ficha | None:
    """Placar do backtest das regras (ultima execucao do gerar-insights)."""
    placar = ctx.base.placar
    if not placar:
        return None
    linhas = []
    for p in placar:
        ic = ("—" if p["ic_acerto_inferior"] is None else
              f"{pct_sem_sinal(float(p['ic_acerto_inferior']), 0)} a {pct_sem_sinal(float(p['ic_acerto_superior']), 0)}")
        acerto = (None if not p["acertos"] or not p["avaliados"] else p["acertos"] / p["avaliados"])
        linhas.append([p["recomendacao"], p["periodo"], str(p["horizonte"]), str(p["avaliados"]),
                       pct_sem_sinal(acerto, 0), ic,
                       pct(None if p["excesso_medio_carteira"] is None else float(p["excesso_medio_carteira"]))])
    versoes = sorted({p["versao_regra"] for p in placar})
    cabecalho = {"tipo": "evidencia", "evidencia": "regras/backtest", "versoes_regra": versoes,
                 "disponivel_ate": ctx.base.ate, "fonte": ["backtest_placar"]}
    secoes = [
        ("Resumo", "Placar da última execução do backtest das regras determinísticas (gerar-insights). "
                   "Nenhuma regra tem vantagem distinguível quando o IC do acerto inclui a taxa-base (DEC-07/08/09 "
                   "do gerar-insights); toda opinião segue experimental."),
        ("Resultado", tabela(["Sinal", "Período", "Pregões", "n", "Acerto", "IC 95% acerto", "Excesso vs carteira"],
                             linhas)),
        ("Limitações", "- Números da última execução gravada em `backtest_placar`; rodar o backtest de novo muda a "
                       "ficha (hash). n pequeno em CALIBRACAO é esperado.\n- Ano corrente fora."),
    ]
    return Ficha("evidencia/regras-backtest.md", cabecalho, secoes)


def montar_todas(ctx: Contexto) -> list[Ficha]:
    idx = Precos(ctx.ajustadas)
    fichas = [montar_fator(ctx, idx, c) for c in sorted(ctx.base.fator_definicao)]
    fichas += [montar_momentum_semanal(ctx, idx), montar_regras(ctx)]
    return [f for f in fichas if f]


__all__ = ["montar_todas", "estatistica", "quintis", "num"]
