"""RAG das fichas (TASK-IA-10): indice incremental e busca com ponto no tempo."""

from __future__ import annotations

from datetime import date

from app.rag import busca, indexador, trechos

ATIVO = """---
tipo: ativo
simbolo: WEGE3
setor: "Emp. Adm. Part. - Máqs., Equip., Veíc. e Peças"
disponivel_ate: 2025-02-26
gerado_em: 2026-10-07
hash: x
---

## Resumo

WEGE3 — WEG S.A.; retorno acumulado alto e beta baixo.

## Por ano

| Ano | Disp. | Retorno | P/L fim |
|---|---|---|---|
| 2023 | 23/02/24 | -4,2% | 27,0 |
| 2024 | 26/02/25 | +43,0% | 36,6 |

## Limitações

- Ano corrente fora.
"""

EVIDENCIA = """---
tipo: evidencia
evidencia: fator/MOMENTO_12_1
disponivel_ate: 2025-12-31
gerado_em: 2026-10-07
hash: y
---

## Resumo

Momentum de 12 meses: spread entre quintis sem vantagem distinguível do acaso.
"""


def _conhecimento(tmp_path, evidencia=True):
    raiz = tmp_path / "conhecimento"
    (raiz / "ativos").mkdir(parents=True)
    (raiz / "ativos" / "WEGE3.md").write_text(ATIVO, encoding="utf-8")
    if evidencia:
        (raiz / "evidencia").mkdir()
        (raiz / "evidencia" / "fator-momento-12-1.md").write_text(EVIDENCIA, encoding="utf-8")
    return raiz


class EmbedderFalso:
    """Bag-of-words em 64 dimensoes: deterministico, sem rede."""
    modelo = "falso"

    def vetores(self, textos):
        saida = []
        for texto in textos:
            v = [0.0] * 64
            for palavra in texto.lower().split():
                v[hash(palavra) % 64] += 1.0
            saida.append(v)
        return saida


class TestTrechos:
    def test_secoes_e_uma_linha_por_ano_com_a_data_da_coluna_disp(self):
        ts = {t.trecho_id: t for t in trechos.da_ficha("ativos/WEGE3.md", ATIVO)}
        assert set(ts) == {"ativos/WEGE3#resumo", "ativos/WEGE3#por-ano/2023", "ativos/WEGE3#por-ano/2024",
                           "ativos/WEGE3#limitacoes"}
        assert ts["ativos/WEGE3#por-ano/2023"].disponivel_ate == date(2024, 2, 23)
        assert ts["ativos/WEGE3#resumo"].disponivel_ate == date(2025, 2, 26)
        assert ts["ativos/WEGE3#por-ano/2024"].fonte == "conhecimento/ativos/WEGE3.md#por-ano"
        assert "| Ano | Disp." in ts["ativos/WEGE3#por-ano/2024"].texto  # cabecalho vai junto
        assert ts["ativos/WEGE3#resumo"].setor.startswith("Emp. Adm. Part.")


class TestPontoNoTempo:
    def test_trecho_com_disponibilidade_futura_nunca_retorna(self, tmp_path):
        idx = tmp_path / "rag.sqlite"
        indexador.indexar(_conhecimento(tmp_path), idx)
        # em 30/06/2024 a linha de 2024 (publica em 26/02/2025) e o resumo nao existem ainda
        achados = busca.buscar("retorno P/L WEGE3", disponivel_ate=date(2024, 6, 30), k=10, indice=idx)
        ids = {t.trecho_id for t in achados}
        assert "ativos/WEGE3#por-ano/2023" in ids
        assert all(t.disponivel_ate <= date(2024, 6, 30) for t in achados)
        assert "ativos/WEGE3#por-ano/2024" not in ids
        depois = busca.buscar("retorno P/L WEGE3", disponivel_ate=date(2025, 3, 1), k=10, indice=idx)
        assert "ativos/WEGE3#por-ano/2024" in {t.trecho_id for t in depois}

    def test_filtros_de_metadado(self, tmp_path):
        idx = tmp_path / "rag.sqlite"
        indexador.indexar(_conhecimento(tmp_path), idx)
        so_evidencia = busca.buscar("momentum", disponivel_ate=date(2026, 1, 1), tipo="evidencia", indice=idx)
        assert [t.trecho_id for t in so_evidencia] == ["evidencia/fator-momento-12-1#resumo"]
        assert busca.buscar("momentum", disponivel_ate=date(2026, 1, 1), simbolo="PETR4", indice=idx) == []

    def test_por_metadado_le_o_resumo_sem_busca(self, tmp_path):
        idx = tmp_path / "rag.sqlite"
        indexador.indexar(_conhecimento(tmp_path), idx)
        resumo = busca.por_metadado(disponivel_ate=date(2026, 1, 1), simbolo="WEGE3", indice=idx)
        assert [t.trecho_id for t in resumo] == ["ativos/WEGE3#resumo"]
        assert busca.por_metadado(disponivel_ate=date(2024, 12, 31), simbolo="WEGE3", indice=idx) == []


class TestIncremental:
    def test_reindexar_sem_mudanca_nao_regrava_e_remove_o_que_sumiu(self, tmp_path):
        raiz = _conhecimento(tmp_path)
        idx = tmp_path / "rag.sqlite"
        primeiro = indexador.indexar(raiz, idx)
        assert primeiro.novos == primeiro.total == 5 and not primeiro.com_vetor
        segundo = indexador.indexar(raiz, idx)
        assert segundo.novos == 0 and segundo.inalterados == 5
        (raiz / "evidencia" / "fator-momento-12-1.md").unlink()
        terceiro = indexador.indexar(raiz, idx)
        assert terceiro.removidos == 1
        assert busca.buscar("momentum", disponivel_ate=date(2026, 1, 1), tipo="evidencia", indice=idx) == []

    def test_com_vetor_e_reaproveita_quando_nada_muda(self, tmp_path):
        raiz = _conhecimento(tmp_path)
        idx = tmp_path / "rag.sqlite"
        r = indexador.indexar(raiz, idx, EmbedderFalso())
        assert r.com_vetor and r.novos == 5
        assert indexador.indexar(raiz, idx, EmbedderFalso()).novos == 0
        achados = busca.buscar("momentum quintis", disponivel_ate=date(2026, 1, 1), k=2, indice=idx,
                               embedder=EmbedderFalso())
        assert achados[0].trecho_id == "evidencia/fator-momento-12-1#resumo"
        assert achados[0].pontuacao > 0

    def test_trecho_id_estavel_entre_reindexacoes(self, tmp_path):
        raiz = _conhecimento(tmp_path)
        a = {t.trecho_id for t in trechos.do_diretorio(raiz)}
        b = {t.trecho_id for t in trechos.do_diretorio(raiz)}
        assert a == b
