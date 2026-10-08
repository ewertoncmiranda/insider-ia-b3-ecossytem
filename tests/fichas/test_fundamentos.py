"""TASK-IA-09: fichas de fundamentos a partir do JSON exportado do painel (sem Node, sem MySQL)."""

from __future__ import annotations

from datetime import date

from app.fichas import fundamentos
from app.fichas.ficha import gravar
from app.rag.trechos import da_ficha

DADOS = {
    "glossario": [{"id": "indicadores", "titulo": "Indicadores", "resumo": "Múltiplos básicos.", "termos": [
        {"termo": "P/L", "definicao": "Preço dividido pelo <strong>lucro</strong> por ação.",
         "exemplo": "P/L 10: dez anos de lucro.", "cuidado": "Lucro negativo deixa o P/L sem sentido.",
         "onde": "Aba Fundamentos."},
        {"termo": "P/L", "definicao": "Verbete repetido."},
    ]}],
    "academico": [{"id": "academico-curvas", "titulo": "Curvas", "resumo": "Juros.", "termos": [
        {"termo": "Fator de desconto", "definicao": "Valor presente de uma unidade futura."}]}],
    "padroes": [{"id": "doji", "termo": "Doji", "fundamento": "Empate.", "indica": "Indecisão.",
                 "cenarios": ["Topo de tendência", "Suporte"], "combinaCom": ["harami"], "nestePainel": "Corpo <= 10%."}],
    "formulas": [{"id": "valuation", "titulo": "Valuation", "resumo": "Preço x lucro.", "fonte": "CVM", "itens": [
        {"nome": "Graham Number", "status": "implementado", "cenarios": ["LONGO_PRAZO"],
         "descricao": "Teto de Graham.", "formula": "sqrt(22,5 x LPA x VPA)"}]}],
    "cursos": [{"id": "historia", "titulo": "História do mercado", "autoria": "Autor", "ano": "2015", "paginas": 17,
                "descricao": "Formação do mercado.", "pdf": "assets/pdfs/01-historia.pdf", "modulos": [
                    {"titulo": "Origens", "aulas": [{"titulo": "Poupança", "paginas": [1, 3], "objetivo": "Relacionar.",
                                                     "topicos": ["Poupança", "Juros"]}]}]}],
}


def fichas():
    return {f.caminho: f for f in fundamentos.montar_todas(DADOS)}


def test_uma_ficha_por_grupo_tema_e_curso():
    assert sorted(fichas()) == [
        "fundamentos/academico/academico-curvas.md", "fundamentos/estudos/historia.md",
        "fundamentos/formulas/valuation.md", "fundamentos/glossario/indicadores.md", "fundamentos/padroes/velas.md"]


def test_trechos_tem_fonte_secao_e_valem_em_qualquer_pregao():
    f = fichas()["fundamentos/glossario/indicadores.md"]
    trechos = da_ficha(f.caminho, f.texto(date(2026, 10, 8)))
    ids = [t.trecho_id for t in trechos]
    assert ids == ["fundamentos/glossario/indicadores#resumo", "fundamentos/glossario/indicadores#p-l",
                   "fundamentos/glossario/indicadores#p-l-2"]  # titulo repetido nao colide
    p_l = trechos[1]
    assert p_l.fonte == "conhecimento/fundamentos/glossario/indicadores.md#p-l"
    assert p_l.tipo == "fundamentos" and p_l.disponivel_ate == date(2000, 1, 1)
    assert "Preço dividido pelo lucro por ação." in p_l.texto  # sem HTML
    assert "**Cuidado:** Lucro negativo" in p_l.texto and "**Onde aparece no painel:** Aba Fundamentos." in p_l.texto


def test_cabecalho_guarda_a_origem_no_painel():
    f = fichas()["fundamentos/formulas/valuation.md"]
    assert f.cabecalho["origem"] == "painel-ativos-frontend/public/js/pages/FormulasPage.js"
    texto = f.texto(date(2026, 10, 8))
    assert "**Fórmula:** sqrt(22,5 x LPA x VPA)" in texto
    assert "**Contextos de uso:** Longo prazo" in texto


def test_estudo_aponta_pdf_e_paginas_sem_copiar_o_texto():
    f = fichas()["fundamentos/estudos/historia.md"]
    assert f.cabecalho["pdf"] == "painel-ativos-frontend/public/assets/pdfs/01-historia.pdf"
    titulo, corpo = f.secoes[1]
    assert titulo == "Origens — Poupança"
    assert "**Páginas do PDF:** 1–3" in corpo and "**Tópicos:** Poupança; Juros" in corpo


def test_hash_estavel_em_reexecucao(tmp_path):
    hoje = date(2026, 10, 8)
    primeira = [gravar(f, tmp_path, hoje) for f in fundamentos.montar_todas(DADOS)]
    segunda = [gravar(f, tmp_path, date(2026, 10, 9)) for f in fundamentos.montar_todas(DADOS)]
    assert all(primeira) and not any(segunda)
    assert "gerado_em: 2026-10-08" in (tmp_path / "fundamentos/padroes/velas.md").read_text(encoding="utf-8")


def test_cli_com_json(tmp_path):
    import json

    entrada = tmp_path / "painel.json"
    entrada.write_text(json.dumps(DADOS, ensure_ascii=False), encoding="utf-8")
    assert fundamentos.main(["--json", str(entrada), "--saida", str(tmp_path / "saida")]) == 0
    assert len(list((tmp_path / "saida" / "fundamentos").rglob("*.md"))) == 5
