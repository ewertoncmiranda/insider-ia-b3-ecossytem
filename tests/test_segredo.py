"""TASK-IA-28: a chave do Gemini nunca vaza (DEC-IA-09).

Com uma chave falsa no ambiente, percorre os caminhos que tocam o Gemini - sucesso, 429 (com a chave
na mensagem do Google), 5xx, timeout, falha qualquer e chat em streaming - capturando todo o log
(nivel DEBUG, todos os loggers) e as respostas HTTP. A chave nao pode aparecer em nenhum deles.

O cliente do SDK e trocado por um falso em `app.provedores.gemini.criar_cliente`, o ponto por onde
todo provedor Gemini nasce: nenhuma chamada sai para a rede.
"""

from __future__ import annotations

import json
import logging
import traceback
import uuid
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

from app.provedores import cadeia as cadeia_mod
from app.provedores import gemini as gemini_mod

CHAVE = "AIzaSyFAKE-segredo-de-teste-9f8e7d6c5b4a"
MIOLO = "segredo-de-teste-9f8e7d6c5b4a"  # pega a chave mesmo cortada ou com prefixo trocado
DOSSIES = Path(__file__).resolve().parents[1] / "avaliacao" / "dossies" / "2026-10-06.jsonl"

try:
    from google.genai import errors as erros_sdk
except ImportError:  # pragma: no cover - o CI instala o google-genai
    erros_sdk = None


def erro_http(codigo: int, mensagem: str, detalhes: list | None = None) -> Exception:
    """Erro no formato do SDK (o real, se instalado), com a chave dentro da mensagem do Google."""
    corpo = {"error": {"code": codigo, "message": mensagem, "status": "X", "details": detalhes or []}}
    if erros_sdk is not None:
        classe = erros_sdk.ClientError if codigo < 500 else erros_sdk.ServerError
        return classe(codigo, corpo)
    erro = Exception(f"{codigo} {corpo}")
    erro.code, erro.details, erro.message = codigo, corpo, mensagem
    return erro


RESPOSTA_OK = json.dumps({"opiniao": "SINAL_NEUTRO", "risco": "RISCO_ALTO", "justificativa": [],
                          "o_que_invalida": [], "dados_ausentes": []})

CENARIOS = {
    "sucesso": None,
    "429": erro_http(429, f"Quota exceeded for key {CHAVE}",
                     [{"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "7s"}]),
    "429_diario": erro_http(429, f"Quota exceeded per day. key={CHAVE}",
                            [{"violations": [{"quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier"}]}]),
    "400_chave_invalida": erro_http(400, f"API key not valid. Please pass a valid API key. ({CHAVE})"),
    "500": erro_http(500, f"Internal error while serving key={CHAVE}"),
    "timeout": httpx.ReadTimeout(f"timed out: https://generativelanguage.googleapis.com/v1beta?key={CHAVE}"),
    "rede": httpx.ConnectError(f"connection refused (x-goog-api-key: {CHAVE})"),
    "qualquer": RuntimeError(f"falha inesperada com {CHAVE}"),
}


class ModelosFalsos:
    def __init__(self, erro: BaseException | None):
        self.erro = erro

    def generate_content(self, **kw):
        if self.erro:
            raise self.erro
        return SimpleNamespace(text=RESPOSTA_OK)

    def generate_content_stream(self, **kw):
        yield SimpleNamespace(text="O P/L divide o preço pelo lucro por ação.")
        if self.erro:
            raise self.erro


def assert_sem_chave(*textos: object) -> None:
    for texto in textos:
        texto = str(texto)
        assert CHAVE not in texto
        assert MIOLO not in texto


def texto_do_erro(erro: BaseException) -> str:
    """O que um log com `exc_info` imprimiria."""
    return "".join(traceback.format_exception(erro)) + repr(erro)


@pytest.fixture
def ambiente(tmp_path, monkeypatch, caplog):
    monkeypatch.setenv("GEMINI_API_KEY", CHAVE)
    monkeypatch.setenv("GEMINI_MODELOS", "gemini-teste-1,gemini-teste-2")
    monkeypatch.setenv("GEMINI_LIMITES", "15/500,5/20")
    monkeypatch.setenv("PROVEDORES_LOTE", "gemini")  # sem Ollama: a cadeia cai direto na regra
    monkeypatch.setenv("OLLAMA_URL", "http://127.0.0.1:1")
    monkeypatch.setenv("RAG_INDICE", str(tmp_path / "rag.sqlite"))  # sem indice; cota.sqlite aqui
    monkeypatch.setattr(cadeia_mod, "_GOVERNADOR", None)
    caplog.set_level(logging.DEBUG)
    return caplog


def usar_cenario(monkeypatch, nome: str) -> None:
    falso = SimpleNamespace(models=ModelosFalsos(CENARIOS[nome]))
    monkeypatch.setattr(gemini_mod, "criar_cliente", lambda chave, timeout_s=30: falso)


def pedido_v10() -> dict:
    return json.loads(DOSSIES.read_text(encoding="utf-8").splitlines()[0])


def pedido_v11() -> dict:
    d = pedido_v10()
    horizonte = {k: d[k] for k in ("evidencias", "permitidas", "risco_calculado", "motivo_sem_base")}
    return {"simbolo": d["simbolo"], "data_pregao": d["data_pregao"], "uso": "lote",
            "dados_ausentes": d["dados_ausentes"], "versao_regra": d["versao_regra"],
            "horizontes": [{"horizonte_pregoes": h, **horizonte} for h in (21, 63, 126)]}


# --- provedor e cadeia, sem HTTP ---------------------------------------------------------------


@pytest.mark.parametrize("nome", [n for n in CENARIOS if n != "sucesso"])
def test_provedor_nao_vaza_em_erro_nem_em_log(ambiente, monkeypatch, nome):
    usar_cenario(monkeypatch, nome)
    provedor, = gemini_mod.criar_provedores(CHAVE, ["gemini-teste-1"])
    with pytest.raises(Exception) as gerar:
        provedor.gerar("sistema", "usuario", {"type": "object"})
    fluxo = provedor.conversar([{"papel": "usuario", "texto": "oi"}], "sistema")
    next(fluxo)
    with pytest.raises(Exception) as conversar:
        next(fluxo)
    logging.getLogger("ia-opiniao").exception("falha do provedor", exc_info=gerar.value)
    assert_sem_chave(texto_do_erro(gerar.value), texto_do_erro(conversar.value), repr(provedor), ambiente.text)


@pytest.mark.parametrize("nome", list(CENARIOS))
def test_cadeia_com_governador_nao_vaza(ambiente, monkeypatch, tmp_path, nome):
    from app.config import Settings

    usar_cenario(monkeypatch, nome)
    settings = Settings.do_ambiente()
    assert_sem_chave(repr(settings), str(settings))
    cadeia = cadeia_mod.montar_cadeia(settings, "lote")
    assert cadeia is not None and [e.nome for e in cadeia.elos] == ["gemini-teste-1", "gemini-teste-2"]
    for elo in cadeia.elos:
        try:
            resposta = cadeia.chamar(elo, "lote", "sistema", "usuario", {"type": "object"})
            assert_sem_chave(resposta)
        except Exception as erro:  # noqa: BLE001 - o que importa e o texto do erro
            logging.getLogger("ia-opiniao").warning("elo falhou: %s", erro, exc_info=erro)
            assert_sem_chave(texto_do_erro(erro))
    assert_sem_chave(ambiente.text, json.dumps(cadeia.governador.estado_modelos()))


# --- rotas HTTP ----------------------------------------------------------------------------------


@pytest.mark.parametrize("nome", list(CENARIOS))
def test_opiniao_v10_e_v11_nao_vazam(ambiente, monkeypatch, nome):
    from app.api import app

    usar_cenario(monkeypatch, nome)
    cliente = TestClient(app)
    r10 = cliente.post("/opiniao", json=pedido_v10())
    r11 = cliente.post("/opiniao/ativo", json=pedido_v11())
    assert r10.status_code == 200 and r11.status_code == 200
    assert_sem_chave(r10.text, r11.text, r10.headers, r11.headers, ambiente.text)


def test_saude_nao_mostra_a_chave(ambiente, monkeypatch):
    from app.api import app

    usar_cenario(monkeypatch, "sucesso")
    resposta = TestClient(app).get("/saude")
    assert resposta.status_code == 200
    assert_sem_chave(resposta.text, ambiente.text)


@pytest.mark.parametrize("nome", ["sucesso", "429", "500", "timeout", "qualquer"])
def test_chat_nao_vaza(ambiente, monkeypatch, nome):
    from app.api import app

    if not any(getattr(rota, "path", None) == "/chat" for rota in app.routes):
        pytest.skip("POST /chat ainda nao existe neste build (TASK-IA-30)")
    usar_cenario(monkeypatch, nome)
    corpo = {"sessao_id": str(uuid.uuid4()), "mensagem": "O que é P/L?", "simbolo": None}
    with TestClient(app).stream("POST", "/chat", json=corpo) as resposta:
        texto = "".join(resposta.iter_text())
    assert_sem_chave(texto, resposta.headers, ambiente.text)
