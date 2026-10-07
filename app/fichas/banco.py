"""Leitura do MySQL para as fichas (DEC-IA-05): uma carga so, so leitura.

Conecta com o usuario `leitor_ia` (GRANT SELECT; criado pela rotina da infra,
senha fora do git). O `pymysql` e importado so aqui dentro: os testes das
fichas sao puros e rodam sem banco nem driver.

Ponto no tempo (SPEC 6.4): nada depois de `ate` (31/12 do ultimo ano fechado)
entra - preco, balanco, provento, evento ou fator.
"""

from __future__ import annotations

import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date

from app.fichas.precos import Serie

CONFIANCA_MINIMA_EVENTO = 0.8


@dataclass
class Balanco:
    ano: int
    data_entrega: date | None
    lucro: float | None
    patrimonio: float | None
    receita: float | None
    ebit: float | None
    divida_liquida: float | None
    lpa: float | None
    vpa: float | None
    roe: float | None
    margem: float | None
    acoes: int | None


@dataclass
class BaseDeDados:
    ate: date
    universo: list[str]                                   # liquidez + DFP anual
    precos: dict[str, Serie]                              # brutos (para P/L e DY)
    eventos: dict[str, list[tuple[date, float, str, float]]]  # (efeito, fator_preco, tipo, fator_acoes)
    eventos_total: int
    balancos: dict[str, list[Balanco]]
    proventos_por_acao: dict[str, dict[int, tuple[float, date | None]]]  # simbolo -> ano -> (soma, maior entrega)
    empresa: dict[str, tuple[str, str | None, str | None]]  # simbolo -> (cnpj, nome, setor_cvm)
    grupo_setor: dict[str, str]                           # setor_cvm -> grupo
    macro: dict[str, list[tuple[date, float]]] = field(default_factory=dict)
    fatores: dict[str, dict[date, dict[str, float]]] = field(default_factory=dict)  # codigo -> data -> simbolo -> valor
    fator_definicao: dict[str, tuple[str, int, str]] = field(default_factory=dict)  # codigo -> (familia, direcao, descricao)
    fator_mercado: dict[str, list[tuple[date, float]]] = field(default_factory=dict)
    placar: list[dict] = field(default_factory=list)


def conectar():
    import pymysql  # so o job precisa do driver

    return pymysql.connect(
        host=os.getenv("DB_HOST", "mysql"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "leitor_ia"),
        password=os.environ["DB_PASS"],
        database=os.getenv("DB_NAME", "minha_base"),
        charset="utf8mb4",
        read_timeout=600,
    )


def _f(valor) -> float | None:
    return None if valor is None else float(valor)


def carregar(conexao, ate: date) -> BaseDeDados:
    cur = conexao.cursor()

    def consulta(sql: str, *parametros):
        cur.execute(sql, parametros)
        return cur.fetchall()

    universo = [s for (s,) in consulta(
        "SELECT DISTINCT fv.simbolo FROM fator_valor fv "
        "WHERE fv.fator_codigo = 'LIQUIDEZ_63D' AND fv.data_referencia <= %s "
        "AND EXISTS (SELECT 1 FROM indicador_fundamentalista i WHERE i.simbolo = fv.simbolo "
        "AND i.tipo_periodo = 'ANUAL' AND YEAR(i.periodo) <= %s) ORDER BY fv.simbolo",
        ate, ate.year)]

    precos: dict[str, Serie] = defaultdict(list)
    for simbolo, dia, fechamento in consulta(
        "SELECT simbolo, data_pregao, fechamento FROM cotacao_b3_diaria "
        "WHERE data_pregao <= %s AND fechamento > 0 AND simbolo IN (SELECT DISTINCT simbolo FROM fator_valor "
        "WHERE fator_codigo = 'LIQUIDEZ_63D') ORDER BY simbolo, data_pregao", ate):
        precos[simbolo].append((dia, float(fechamento)))

    eventos: dict[str, list] = defaultdict(list)
    for simbolo, dia, fator_preco, tipo, fator_acoes in consulta(
        "SELECT simbolo, data_efeito, fator_preco, tipo, fator_acoes FROM evento_corporativo "
        "WHERE data_efeito <= %s AND (confianca IS NULL OR confianca >= %s) ORDER BY data_efeito",
        ate, CONFIANCA_MINIMA_EVENTO):
        eventos[simbolo].append((dia, float(fator_preco), tipo, float(fator_acoes)))
    (eventos_total,), = consulta("SELECT COUNT(*) FROM evento_corporativo")

    balancos: dict[str, list[Balanco]] = defaultdict(list)
    for linha in consulta(
        "SELECT simbolo, YEAR(periodo), data_entrega, lucro_liquido, patrimonio_liquido, receita_liquida, ebit, "
        "divida_liquida, lpa, vpa, roe, margem_liquida, acoes_ex_tesouraria FROM indicador_fundamentalista "
        "WHERE tipo_periodo = 'ANUAL' AND YEAR(periodo) <= %s ORDER BY simbolo, periodo", ate.year):
        simbolo, ano, entrega, *valores = linha
        balancos[simbolo].append(Balanco(int(ano), entrega, *[_f(v) for v in valores[:-1]],
                                         int(valores[-1]) if valores[-1] is not None else None))

    empresa = {}
    for simbolo, cnpj, nome, setor in consulta(
        "SELECT t.simbolo, t.cnpj, e.denominacao, e.setor FROM cvm_ticker t "
        "LEFT JOIN cvm_empresa e ON e.cnpj = t.cnpj"):
        empresa[simbolo] = (cnpj, nome, setor)
    for simbolo, cnpj in consulta("SELECT DISTINCT simbolo, cnpj FROM indicador_fundamentalista"):
        empresa.setdefault(simbolo, (cnpj, None, None))

    proventos: dict[str, dict[int, tuple[float, date | None]]] = defaultdict(dict)
    cnpj_para_simbolos: dict[str, list[str]] = defaultdict(list)
    for simbolo, (cnpj, _, _) in empresa.items():
        cnpj_para_simbolos[cnpj].append(simbolo)
    for cnpj, ano, soma, entrega in consulta(
        "SELECT cnpj, YEAR(dt_fim_exerc), SUM(por_acao), MAX(data_entrega) FROM provento_contabil "
        "WHERE YEAR(dt_fim_exerc) <= %s AND por_acao IS NOT NULL GROUP BY cnpj, YEAR(dt_fim_exerc)", ate.year):
        for simbolo in cnpj_para_simbolos.get(cnpj, []):
            proventos[simbolo][int(ano)] = (float(soma), entrega)

    grupo_setor = {s: g for s, g in consulta("SELECT setor_cvm, grupo_setor FROM setor_grupo")}

    macro: dict[str, list] = defaultdict(list)
    for codigo, dia, valor in consulta(
        "SELECT codigo_serie, data, valor FROM indice_macro WHERE codigo_serie IN ('CDI','SELIC','IPCA') "
        "AND data <= %s AND valor IS NOT NULL ORDER BY codigo_serie, data", ate):
        macro[codigo].append((dia, float(valor)))

    fatores: dict[str, dict[date, dict[str, float]]] = defaultdict(lambda: defaultdict(dict))
    for codigo, dia, simbolo, valor in consulta(
        "SELECT fator_codigo, data_referencia, simbolo, valor FROM fator_valor "
        "WHERE data_referencia <= %s AND valor IS NOT NULL", ate):
        fatores[codigo][dia][simbolo] = float(valor)

    definicao = {c: (f, int(d), desc) for c, f, d, desc in consulta(
        "SELECT codigo, familia, direcao_esperada, descricao FROM fator_definicao WHERE ativo")}

    fator_mercado: dict[str, list] = defaultdict(list)
    for codigo, dia, retorno in consulta(
        "SELECT fator_codigo, data_referencia, retorno FROM fator_mercado_mensal "
        "WHERE data_referencia <= %s ORDER BY fator_codigo, data_referencia", ate):
        fator_mercado[codigo].append((dia, float(retorno)))

    colunas = ("versao_regra", "periodo", "recomendacao", "horizonte", "avaliados", "acertos", "taxa_base",
               "excesso_medio_carteira", "ic_acerto_inferior", "ic_acerto_superior",
               "ic_excesso_carteira_inferior", "ic_excesso_carteira_superior", "meses_bootstrap")
    placar = [dict(zip(colunas, linha)) for linha in consulta(
        f"SELECT {', '.join('p.' + c for c in colunas)} FROM backtest_placar p "
        "WHERE p.execucao_id = (SELECT MAX(execucao_id) FROM backtest_placar) "
        "ORDER BY p.recomendacao, p.periodo, p.horizonte")]

    cur.close()
    return BaseDeDados(
        ate=ate, universo=universo, precos=dict(precos), eventos=dict(eventos), eventos_total=int(eventos_total),
        balancos=dict(balancos), proventos_por_acao=dict(proventos), empresa=empresa, grupo_setor=grupo_setor,
        macro=dict(macro), fatores={k: dict(v) for k, v in fatores.items()}, fator_definicao=definicao,
        fator_mercado=dict(fator_mercado), placar=placar,
    )
