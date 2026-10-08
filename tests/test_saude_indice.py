"""/saude mostra o tamanho e a data do indice do RAG (REQ-IA-08)."""

import sqlite3

from fastapi.testclient import TestClient

from app.api import app


def test_saude_sem_indice_mostra_zero(monkeypatch, tmp_path):
    monkeypatch.setenv("RAG_INDICE", str(tmp_path / "nao-existe.sqlite"))
    assert TestClient(app).get("/saude").json()["indice"] == {"trechos": 0, "ultima_indexacao": None}


def test_saude_com_indice_conta_trechos_e_data(monkeypatch, tmp_path):
    caminho = tmp_path / "rag.sqlite"
    con = sqlite3.connect(caminho)
    con.execute("CREATE TABLE trecho (trecho_id TEXT)")
    con.executemany("INSERT INTO trecho VALUES (?)", [("a",), ("b",), ("c",)])
    con.commit()
    con.close()
    monkeypatch.setenv("RAG_INDICE", str(caminho))
    indice = TestClient(app).get("/saude").json()["indice"]
    assert indice["trechos"] == 3 and indice["ultima_indexacao"].endswith("+00:00")
