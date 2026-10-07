"""TASK-IA-01: /saude e /skills respondem sem Ollama e refletem o diretorio de skills."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app import skills as skills_mod
from app.api import app

cliente = TestClient(app)


def test_saude_responde_200_degradado_sem_ollama(monkeypatch):
    monkeypatch.setenv("OLLAMA_URL", "http://127.0.0.1:1")
    resposta = cliente.get("/saude")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "DEGRADADO"
    assert corpo["ollama"]["alcancavel"] is False
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
