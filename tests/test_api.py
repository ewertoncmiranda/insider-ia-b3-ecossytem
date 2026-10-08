"""TASK-IA-01: /saude e /skills respondem sem Gemini e refletem o diretorio de skills."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app import skills as skills_mod
from app.api import app

cliente = TestClient(app)


def test_saude_responde_200_degradado_sem_gemini(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    resposta = cliente.get("/saude")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "DEGRADADO" and corpo["modelo"] == "regra"
    assert corpo["provedores"]["gemini"] == {"configurado": False, "modelos": []}
    assert corpo["provedores"]["ordem_lote"] == ["gemini"] and "ollama" not in corpo
    assert corpo["cota"]["chat"] == {"restante_hoje": None}
    assert corpo["skills_versao"].startswith("skills@")
    assert "regra experimental" in corpo["aviso"]


def test_skills_vazio_tem_versao_estavel(tmp_path, monkeypatch):
    monkeypatch.setenv("DIR_SKILLS", str(tmp_path))
    a = cliente.get("/skills").json()
    b = cliente.get("/skills").json()
    assert a["skills"] == [] and a["versao"] == b["versao"]


def test_hash_muda_quando_o_conteudo_da_skill_muda(tmp_path, monkeypatch):
    pasta = tmp_path / "leitura-tecnica"
    pasta.mkdir()
    (pasta / "SKILL.md").write_text("---\nversao: 1.0\n---\nTexto A", encoding="utf-8")
    monkeypatch.setenv("DIR_SKILLS", str(tmp_path))
    antes = cliente.get("/skills").json()
    assert antes["skills"][0]["nome"] == "leitura-tecnica"
    assert antes["skills"][0]["versao"] == "1.0"
    (pasta / "SKILL.md").write_text("---\nversao: 1.0\n---\nTexto B", encoding="utf-8")
    depois = cliente.get("/skills").json()
    assert antes["versao"] != depois["versao"]
    assert len(depois["versao"]) <= 20  # cabe em opiniao_ia.versao_prompt VARCHAR(20)


def test_versao_do_conjunto_vazio_e_deterministica():
    assert skills_mod.versao_do_conjunto([]) == skills_mod.versao_do_conjunto([])


def test_saude_com_gemini_mostra_modelos_e_cota_sem_a_chave(monkeypatch, tmp_path):
    from app.provedores import cadeia

    monkeypatch.setenv("GEMINI_API_KEY", "AIzaFAKE-saude-0123456789abcdef")
    monkeypatch.setenv("GEMINI_MODELOS", "g1,g2")
    monkeypatch.setenv("GEMINI_LIMITES", "15/500,5/20")
    monkeypatch.setenv("PROVEDORES_LOTE", "gemini,ollama")  # .env antigo: ollama e ignorado
    monkeypatch.setenv("RAG_INDICE", str(tmp_path / "rag.sqlite"))
    monkeypatch.setattr(cadeia, "_GOVERNADOR", None)
    resposta = cliente.get("/saude")
    corpo = resposta.json()
    assert corpo["status"] == "OK" and corpo["modelo"] == "g1"
    assert corpo["provedores"]["ordem_lote"] == ["gemini"]
    assert [m["nome"] for m in corpo["provedores"]["gemini"]["modelos"]] == ["g1", "g2"]
    assert corpo["provedores"]["gemini"]["modelos"][1]["teto_dia"] == 20
    assert corpo["cota"]["lote"]["restante_hoje"] >= 208  # 40% de 520 (mais depois das 18h, com a sobra)
    assert "AIza" not in resposta.text
