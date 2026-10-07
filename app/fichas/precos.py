"""Estatisticas de preco para as fichas. Puro: listas de (data, preco) em ordem.

O COTAHIST e bruto; o ajuste por desdobramento/grupamento/bonificacao usa
`evento_corporativo` (confianca >= 0,8, a mesma regra do gerar-insights):
todo preco anterior a data de efeito e multiplicado pelo fator_preco.
Retorno diario acima de SALTO_SUSPEITO depois do ajuste e tratado como dado
suspeito (evento nao inferido ou erro): fica fora das estatisticas e entra
nas Limitacoes da ficha.
"""

from __future__ import annotations

import bisect
import math
from collections import defaultdict
from datetime import date

PREGOES_ANO = 252
SALTO_SUSPEITO = 0.40
MINIMO_MERCADO = 5

Serie = list[tuple[date, float]]


def ajustar(serie: Serie, eventos: list[tuple[date, float]]) -> Serie:
    """eventos: (data_efeito, fator_preco). Precos antes do efeito x fator."""
    if not eventos:
        return list(serie)
    eventos = sorted(eventos)
    datas = [d for d, _ in eventos]
    # fator acumulado dos eventos com efeito DEPOIS de cada dia
    sufixo = [1.0] * (len(eventos) + 1)
    for i in range(len(eventos) - 1, -1, -1):
        sufixo[i] = sufixo[i + 1] * eventos[i][1]
    saida = []
    for dia, preco in serie:
        i = bisect.bisect_right(datas, dia)
        saida.append((dia, preco * sufixo[i]))
    return saida


def retornos_diarios(serie: Serie) -> dict[date, float]:
    saida = {}
    for (_, anterior), (dia, atual) in zip(serie, serie[1:]):
        if anterior > 0 and atual > 0:
            saida[dia] = atual / anterior - 1
    return saida


def saltos(retornos: dict[date, float]) -> list[date]:
    return sorted(d for d, r in retornos.items() if abs(r) > SALTO_SUSPEITO)


def limpos(retornos: dict[date, float]) -> dict[date, float]:
    return {d: r for d, r in retornos.items() if abs(r) <= SALTO_SUSPEITO}


def mercado_igual_peso(retornos_por_papel: dict[str, dict[date, float]]) -> dict[date, float]:
    """Media simples dos retornos limpos do dia, com ao menos 5 papeis."""
    soma: dict[date, float] = defaultdict(float)
    conta: dict[date, int] = defaultdict(int)
    for retornos in retornos_por_papel.values():
        for dia, r in limpos(retornos).items():
            soma[dia] += r
            conta[dia] += 1
    return {d: soma[d] / conta[d] for d in sorted(soma) if conta[d] >= MINIMO_MERCADO}


def composto(retornos: list[float]) -> float | None:
    if not retornos:
        return None
    acumulado = 1.0
    for r in retornos:
        acumulado *= 1 + r
    return acumulado - 1


def por_ano(retornos: dict[date, float]) -> dict[int, list[float]]:
    saida: dict[int, list[float]] = defaultdict(list)
    for dia in sorted(retornos):
        saida[dia.year].append(retornos[dia])
    return dict(saida)


def volatilidade(retornos: list[float]) -> float | None:
    if len(retornos) < 20:
        return None
    media = sum(retornos) / len(retornos)
    var = sum((r - media) ** 2 for r in retornos) / (len(retornos) - 1)
    return math.sqrt(var) * math.sqrt(PREGOES_ANO)


def drawdown_maximo(retornos: list[float]) -> float | None:
    """Maior queda do pico ao vale dentro da sequencia (negativo)."""
    if not retornos:
        return None
    nivel = pico = 1.0
    pior = 0.0
    for r in retornos:
        nivel *= 1 + r
        pico = max(pico, nivel)
        pior = min(pior, nivel / pico - 1)
    return pior


def pior_queda(retornos: dict[date, float]) -> dict | None:
    """Maior drawdown da historia toda, com datas e pregoes ate recuperar."""
    if not retornos:
        return None
    nivel = pico = 1.0
    dias = sorted(retornos)
    dia_pico = dias[0]  # o nivel inicial conta como pico (papel que so cai)
    pior = {"queda": 0.0}
    for dia in dias:
        nivel *= 1 + retornos[dia]
        if nivel >= pico:
            pico, dia_pico = nivel, dia
        queda = nivel / pico - 1
        if queda < pior["queda"]:
            pior = {"queda": queda, "pico": dia_pico, "vale": dia, "nivel_pico": pico}
    if pior["queda"] == 0.0:
        return None
    # recuperacao: primeiro dia depois do vale em que o nivel volta ao pico
    nivel = 1.0
    pior["recuperou"] = None
    for dia in dias:
        nivel *= 1 + retornos[dia]
        if dia > pior["vale"] and nivel >= pior["nivel_pico"]:
            pior["recuperou"] = dia
            break
    if pior["recuperou"]:
        pior["pregoes_recuperacao"] = sum(1 for d in dias if pior["vale"] < d <= pior["recuperou"])
    return pior


def beta(ativo: dict[date, float], mercado: dict[date, float]) -> tuple[float | None, int]:
    comuns = [d for d in ativo if d in mercado]
    if len(comuns) < 60:
        return None, len(comuns)
    xs = [mercado[d] for d in comuns]
    ys = [ativo[d] for d in comuns]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    var = sum((x - mx) ** 2 for x in xs)
    return (cov / var if var else None), len(comuns)


def retorno_a_frente(serie: Serie, dia: date, pregoes: int) -> float | None:
    """Do fechamento do primeiro pregao >= dia ate `pregoes` adiante."""
    datas = [d for d, _ in serie]
    i = bisect.bisect_left(datas, dia)
    j = i + pregoes
    if i >= len(serie) or j >= len(serie) or serie[i][1] <= 0:
        return None
    return serie[j][1] / serie[i][1] - 1


def fechamento_ate(serie: Serie, dia: date) -> tuple[date, float] | None:
    """Ultimo (data, preco) com data <= dia."""
    datas = [d for d, _ in serie]
    i = bisect.bisect_right(datas, dia)
    return serie[i - 1] if i else None


def quantis(valores: list[float], qs: tuple[float, ...] = (0.25, 0.5, 0.75)) -> list[float | None]:
    if not valores:
        return [None] * len(qs)
    v = sorted(valores)
    saida = []
    for q in qs:
        pos = q * (len(v) - 1)
        baixo, alto = math.floor(pos), math.ceil(pos)
        saida.append(v[baixo] + (v[alto] - v[baixo]) * (pos - baixo))
    return saida
