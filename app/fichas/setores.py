"""Ficha de setor (TASK-IA-07, SPEC 6.3): faixas tipicas por ano e retorno
contra o mercado, para comparar um papel com os pares. Puro.

Um arquivo por setor do FCA (`cvm_empresa.setor`) com papeis no universo das
fichas; o grupo de `setor_grupo` (V21) vai no cabecalho.
"""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from datetime import date

from app.fichas import precos
from app.fichas.contexto import Contexto
from app.fichas.ficha import Ficha, num, pct, tabela

FONTES = ["cvm_empresa", "setor_grupo", "indicador_fundamentalista", "cotacao_b3_diaria"]


def slug(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", sem_acento.lower()).strip("-")


def _faixa(valores: list[float], casas: int = 1) -> str:
    if len(valores) < 3:
        return "—" if not valores else num(precos.quantis(valores, (0.5,))[0], casas)
    p25, p50, p75 = precos.quantis(valores)
    return f"{num(p50, casas)} ({num(p25, casas)}–{num(p75, casas)})"


def montar_todas(ctx: Contexto) -> list[Ficha]:
    membros: dict[str, list[str]] = defaultdict(list)
    for simbolo in ctx.base.universo:
        setor = ctx.setor(simbolo)
        if setor:
            membros[setor].append(simbolo)
    return [f for f in (montar(ctx, setor, sorted(ms)) for setor, ms in sorted(membros.items())) if f]


def montar(ctx: Contexto, setor: str, membros: list[str]) -> Ficha | None:
    base = ctx.base
    anos = sorted({a for s in membros for a in precos.por_ano(ctx.retornos.get(s, {}))
                   if a <= base.ate.year})
    if not anos:
        return None
    linhas, excessos = [], {}
    entregas: list[date] = []
    for ano in anos:
        pls, roes, margens, alav, rets = [], [], [], [], []
        disponivel = date(ano, 12, 31)
        for s in membros:
            b = next((x for x in base.balancos.get(s, []) if x.ano == ano), None)
            fim = precos.fechamento_ate(base.precos.get(s, []), date(ano, 12, 31))
            if b:
                if b.data_entrega:
                    entregas.append(b.data_entrega)
                    disponivel = max(disponivel, b.data_entrega)
                if b.lpa and b.lpa > 0 and fim and fim[0].year == ano:
                    pls.append(fim[1] / b.lpa)
                if b.roe is not None:
                    roes.append(b.roe)
                if b.margem is not None:
                    margens.append(b.margem)
                if b.divida_liquida is not None and b.ebit and b.ebit > 0:
                    alav.append(b.divida_liquida / b.ebit)
            rs = precos.por_ano(ctx.retornos.get(s, {})).get(ano)
            if rs and len(rs) > 200:   # so papel com o ano (quase) inteiro
                rets.append(precos.composto(rs))
        ret_setor = sum(rets) / len(rets) if rets else None
        merc = ctx.mercado_por_ano.get(ano)
        if ret_setor is not None and merc is not None:
            excessos[ano] = ret_setor - merc
        linhas.append([str(ano), f"{disponivel:%d/%m/%y}", str(len(rets)), _faixa(pls), _faixa(roes), _faixa(margens), _faixa(alav),
                       pct(ret_setor), pct(excessos.get(ano))])

    grupo = base.grupo_setor.get(setor, "")
    resumo = [f"{setor} (grupo {grupo or '—'}): {len(membros)} papéis no universo das fichas — "
              f"{', '.join(membros[:12])}{'…' if len(membros) > 12 else ''}."]
    if len(excessos) >= 3:
        pico = max(excessos, key=excessos.get)
        vale = min(excessos, key=excessos.get)
        resumo.append(f"Melhor ano contra o mercado: {pico} ({pct(excessos[pico])}); pior: {vale} "
                      f"({pct(excessos[vale])}). Média igual-peso dos papéis com o ano inteiro.")
    n_max = max(int(l[2]) for l in linhas)
    if n_max < 3:
        resumo.append("Poucos papéis: faixas são indicativas, não típicas.")

    cabecalho = {"tipo": "setor", "setor": setor, "grupo_setor": grupo, "papeis": len(membros),
                 "cobertura": f"{anos[0]}-{anos[-1]}",
                 "disponivel_ate": max(entregas + [base.ate]) if entregas else base.ate, "fonte": FONTES}
    secoes = [
        ("Resumo", "\n".join(resumo)),
        ("Por ano", "Disp. = quando a linha ficou pública (entrega da última DFP do ano). Mediana (p25–p75) entre os papéis do setor. P/L só com lucro; alavancagem = dívida "
                    "líquida / EBIT (EBIT positivo).\n\n" + tabela(
                        ["Ano", "Disp.", "Papéis", "P/L fim", "ROE %", "Margem %", "Dív.líq./EBIT", "Retorno", "vs merc."],
                        linhas)),
        ("Limitações", "\n".join([
            "- Setor do FCA atual da empresa (sem histórico de reclassificação).",
            "- Bancos e seguradoras não têm EBIT nem margem comparável: colunas vazias são ausência, não zero.",
            "- Preço ajustado por eventos inferidos (confiança ≥ 0,8); P/L com fechamento bruto de 31/12 e LPA do "
            "exercício, público só na entrega da DFP no ano seguinte.",
            f"- Ano corrente fora; dados até {base.ate:%d/%m/%Y}.",
        ])),
    ]
    return Ficha(f"setores/{slug(setor)}.md", cabecalho, secoes)
