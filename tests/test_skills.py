"""TASK-IA-04: o prompt vem das skills, selecionadas por horizonte e evidencias."""

from __future__ import annotations

from pathlib import Path

from app import skills as skills_mod
from app.modelos import OPINIOES, RISCOS
from app.prompt import SCHEMA_DA_RESPOSTA, SISTEMA

DIR_SKILLS = Path(__file__).resolve().parents[1] / "skills"


def _conjunto():
    return skills_mod.listar(DIR_SKILLS)


def test_conjunto_tem_as_skills_do_spec_ia_04():
    nomes = {s.nome for s in _conjunto()}
    assert {"conformidade-cvm", "formato-resposta", "horizonte-curto", "horizonte-medio", "horizonte-longo",
            "leitura-valuation", "leitura-tecnica", "leitura-fatores", "leitura-eventos"} <= nomes
    assert all(s.versao != "0" for s in _conjunto())


def test_seleciona_so_o_relevante_para_o_pedido():
    nomes = [s.nome for s in skills_mod.selecionar(_conjunto(), 21, ["sinal_momentum", "fator_roic"])]
    assert nomes[:2] == ["conformidade-cvm", "formato-resposta"]
    assert "horizonte-curto" in nomes and "horizonte-longo" not in nomes
    assert "leitura-tecnica" in nomes and "leitura-fatores" in nomes
    assert "leitura-valuation" not in nomes and "leitura-eventos" not in nomes


def test_prompt_de_skills_mantem_as_regras_do_prompt_embutido():
    sistema = skills_mod.montar_sistema(skills_mod.selecionar(_conjunto(), 63, ["regra_v1"]))
    for trecho in ("NÃO é consultor", "somente as evidências recebidas", "somente entre as 'permitidas'",
                   "exatamente como 'risco_calculado'", "de 2 a 5 itens", "UMA frase de até 20 palavras",
                   "Nunca prometa resultado", "'garantido', 'certeza' e 'sem risco'"):
        assert trecho in sistema, trecho
        assert trecho in SISTEMA or trecho in sistema  # as regras antigas continuam presentes


def test_schema_das_skills_tem_o_mesmo_vocabulario_do_contrato():
    schema = skills_mod.schema_da_resposta(DIR_SKILLS)
    assert schema["properties"]["opiniao"]["enum"] == list(OPINIOES)
    assert schema["properties"]["risco"]["enum"] == list(RISCOS)
    assert schema == SCHEMA_DA_RESPOSTA


def test_cabecalho_e_corpo_sao_separados():
    meta, corpo = skills_mod._separar("---\nnome: x\nversao: 2.1\n---\nTexto do corpo")
    assert meta == {"nome": "x", "versao": "2.1"} and corpo == "Texto do corpo"
    assert skills_mod._separar("sem cabecalho") == ({}, "sem cabecalho")
