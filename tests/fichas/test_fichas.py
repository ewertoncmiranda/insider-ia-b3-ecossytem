"""Fichas de anos fechados (TASK-IA-07/08): partes puras, sem banco."""

from __future__ import annotations

from datetime import date, timedelta

from app.fichas import ativos, contexto, evidencia, ficha, precos
from app.fichas.__main__ import main
from app.fichas.banco import Balanco, BaseDeDados


def _serie(inicio: date, precos_: list[float]) -> precos.Serie:
    saida, dia = [], inicio
    for p in precos_:
        while dia.weekday() >= 5:
            dia += timedelta(days=1)
        saida.append((dia, p))
        dia += timedelta(days=1)
    return saida


class TestFicha:
    def test_hash_estavel_e_sem_regravar(self, tmp_path):
        f = ficha.Ficha("ativos/X.md", {"tipo": "ativo", "simbolo": "X"}, [("Resumo", "a")])
        assert f.hash() == ficha.Ficha("ativos/X.md", {"tipo": "ativo", "simbolo": "X"}, [("Resumo", "a")]).hash()
        assert ficha.gravar(f, tmp_path, date(2026, 10, 7)) is True
        texto = (tmp_path / "ativos/X.md").read_text(encoding="utf-8")
        # mesma ficha num outro dia: nao regrava, nem a data de geracao muda
        assert ficha.gravar(f, tmp_path, date(2026, 10, 8)) is False
        assert (tmp_path / "ativos/X.md").read_text(encoding="utf-8") == texto
        assert "gerado_em: 2026-10-07" in texto

    def test_conteudo_novo_regrava(self, tmp_path):
        ficha.gravar(ficha.Ficha("m/a.md", {"tipo": "m"}, [("R", "1")]), tmp_path, date(2026, 1, 1))
        assert ficha.gravar(ficha.Ficha("m/a.md", {"tipo": "m"}, [("R", "2")]), tmp_path, date(2026, 1, 2))

    def test_yaml_escapa_e_formata_listas(self):
        f = ficha.Ficha("x.md", {"setor": "Bancos: varejo", "fonte": ["a", "b"], "n": 3})
        texto = f.texto(date(2026, 1, 1))
        assert 'setor: "Bancos: varejo"' in texto
        assert "fonte: [a, b]" in texto

    def test_formatos_ptbr_e_ausente(self):
        assert ficha.pct(0.1234) == "+12,3%"
        assert ficha.pct(None) == "—"
        assert ficha.num(1.5) == "1,5"


class TestPrecos:
    def test_ajuste_por_desdobramento(self):
        serie = [(date(2024, 4, 15), 56.0), (date(2024, 4, 16), 28.0)]
        ajustada = precos.ajustar(serie, [(date(2024, 4, 16), 0.5)])
        assert ajustada == [(date(2024, 4, 15), 28.0), (date(2024, 4, 16), 28.0)]

    def test_salto_sem_evento_fica_fora(self):
        rets = precos.retornos_diarios(_serie(date(2024, 1, 1), [10, 10.5, 50, 51]))
        assert len(precos.saltos(rets)) == 1
        assert all(abs(r) <= precos.SALTO_SUSPEITO for r in precos.limpos(rets).values())

    def test_pior_queda_de_papel_que_so_cai(self):
        rets = precos.retornos_diarios(_serie(date(2024, 1, 1), [10, 9, 8, 7]))
        queda = precos.pior_queda(rets)
        assert queda["pico"] is not None
        assert round(queda["queda"], 4) == -0.3  # do nivel inicial (10) ao vale (7)
        assert queda["recuperou"] is None

    def test_drawdown_e_quantis(self):
        assert round(precos.drawdown_maximo([0.1, -0.5, 0.2]), 4) == -0.5
        assert precos.quantis([1, 2, 3, 4, 5]) == [2, 3, 4]


class TestEvidencia:
    def test_quintis_no_sentido_da_direcao(self):
        valores = {f"P{i:02d}": float(i) for i in range(25)}
        q1, q5 = evidencia.quintis(valores, 1)
        assert q5[-1] == "P24" and q1[0] == "P00"
        q1, q5 = evidencia.quintis(valores, -1)
        assert q5[-1] == "P00"
        assert evidencia.quintis({"A": 1.0}, 1) is None

    def test_estatistica_com_ic(self):
        e = evidencia.estatistica([0.01, 0.02, 0.03, -0.01])
        assert e["n"] == 4 and e["ic"][0] < e["media"] < e["ic"][1]
        assert evidencia.estatistica([0.1]) is None


def _base_minima(n_dias: int = 600) -> BaseDeDados:
    precos_ = {}
    for k in range(6):
        valores = [10 * (1 + 0.0005 * (k + 1)) ** i for i in range(n_dias)]
        precos_[f"PAP{k}3"] = _serie(date(2023, 1, 2), valores)
    balancos = {s: [Balanco(2023, date(2024, 3, 1), 100.0, 1000.0, 500.0, 120.0, 50.0, 1.0, 10.0, 10.0, 20.0, 100)]
                for s in precos_}
    return BaseDeDados(
        ate=date(2024, 12, 31), universo=sorted(precos_), precos=precos_, eventos={}, eventos_total=89,
        balancos=balancos, proventos_por_acao={}, empresa={s: ("00", "Empresa", "Bancos") for s in precos_},
        grupo_setor={"Bancos": "FINANCEIRO"},
    )


class TestAtivo:
    def test_ficha_de_ativo_cabe_em_4kb_e_declara_limitacoes(self):
        base = _base_minima()
        base.precos = {s: [p for p in serie if p[0] <= base.ate] for s, serie in base.precos.items()}
        ctx = contexto.montar(base)
        f = ativos.montar(ctx, "PAP03")
        texto = f.texto(date(2026, 10, 7))
        assert len(texto.encode("utf-8")) <= ficha.LIMITE_ATIVO_BYTES
        assert "## Limitações" in texto and "89 registros" in texto
        assert "2025" not in f.cabecalho["cobertura"]
        assert f.cabecalho["disponivel_ate"] >= date(2024, 3, 1)


def test_cli_recusa_ano_corrente():
    assert main(["--ate-ano", str(date.today().year)]) == 2
