"""TASK-IA-24: provedor Gemini com cliente falso (nenhuma chamada de rede)."""

from __future__ import annotations

import json
import traceback
from types import SimpleNamespace

import httpx
import pytest

from app.provedores.gemini import ErroDeCota, GeminiProvedor, criar_provedores
from app.provedores.ollama import ErroDoProvedor

CHAVE = "AIzaFAKE-chave-de-teste-0123456789abcdef"
SCHEMA = {"type": "object", "properties": {"opiniao": {"type": "string"}}, "required": ["opiniao"]}


class ErroApi(Exception):
    """Mesmo formato do `google.genai.errors.APIError`: code, message, details (corpo JSON)."""

    def __init__(self, code, details):
        self.code = code
        self.details = details
        self.message = (details.get("error") or {}).get("message", "")
        super().__init__(f"{code}. {details}")


def corpo_429(retry=None, quota_id="GenerateRequestsPerMinutePerProjectPerModel-FreeTier", mensagem=None):
    detalhes = [{"@type": "type.googleapis.com/google.rpc.QuotaFailure",
                 "violations": [{"quotaMetric": "generativelanguage.googleapis.com/generate_content_free_tier_requests",
                                 "quotaId": quota_id}]}]
    if retry:
        detalhes.append({"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": retry})
    return {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED", "details": detalhes,
                      "message": mensagem or f"You exceeded your current quota. key={CHAVE}"}}


class Modelos:
    def __init__(self, resposta=None, erro=None, pedacos=()):
        self.resposta, self.erro, self.pedacos = resposta, erro, pedacos
        self.chamadas = []

    def generate_content(self, **kw):
        self.chamadas.append(kw)
        if self.erro:
            raise self.erro
        return SimpleNamespace(text=self.resposta)

    def generate_content_stream(self, **kw):
        self.chamadas.append(kw)
        for p in self.pedacos:
            if isinstance(p, BaseException):
                raise p
            yield SimpleNamespace(text=p)


def provedor(**kw):
    modelos = Modelos(**kw)
    return GeminiProvedor(SimpleNamespace(models=modelos), "gemini-3.5-flash-lite", chave=CHAVE), modelos


def test_gerar_pede_json_pelo_schema_com_temperatura_zero():
    p, modelos = provedor(resposta=json.dumps({"opiniao": "SINAL_NEUTRO"}))
    assert json.loads(p.gerar("sistema", "usuario", SCHEMA)) == {"opiniao": "SINAL_NEUTRO"}
    chamada = modelos.chamadas[0]
    assert chamada["model"] == "gemini-3.5-flash-lite"
    assert chamada["contents"] == "usuario"
    assert chamada["config"] == {"system_instruction": "sistema", "temperature": 0,
                                 "response_mime_type": "application/json", "response_json_schema": SCHEMA}


def test_429_com_retry_delay():
    p, _ = provedor(erro=ErroApi(429, corpo_429(retry="17s")))
    with pytest.raises(ErroDeCota) as erro:
        p.gerar("s", "u", SCHEMA)
    assert erro.value.espera_s == 17.0
    assert erro.value.diaria is False


def test_429_sem_retry_delay():
    p, _ = provedor(erro=ErroApi(429, corpo_429()))
    with pytest.raises(ErroDeCota) as erro:
        p.gerar("s", "u", SCHEMA)
    assert erro.value.espera_s is None
    assert erro.value.diaria is False


def test_429_de_cota_diaria():
    p, _ = provedor(erro=ErroApi(429, corpo_429(retry="3.5s", quota_id="GenerateRequestsPerDayPerProjectPerModel-FreeTier")))
    with pytest.raises(ErroDeCota) as erro:
        p.gerar("s", "u", SCHEMA)
    assert erro.value.diaria is True
    assert erro.value.espera_s == 3.5


def test_500_vira_erro_do_provedor_e_nao_de_cota():
    p, _ = provedor(erro=ErroApi(500, {"error": {"code": 500, "message": "Internal error", "status": "INTERNAL"}}))
    with pytest.raises(ErroDoProvedor) as erro:
        p.gerar("s", "u", SCHEMA)
    assert not isinstance(erro.value, ErroDeCota)
    assert "HTTP 500" in str(erro.value)


@pytest.mark.parametrize("falha", [httpx.ReadTimeout("lento"), TimeoutError(), httpx.ConnectError("sem rede")])
def test_timeout_e_rede_viram_erro_do_provedor(falha):
    p, _ = provedor(erro=falha)
    with pytest.raises(ErroDoProvedor) as erro:
        p.gerar("s", "u", SCHEMA)
    assert not isinstance(erro.value, ErroDeCota)


def test_resposta_vazia_e_erro():
    p, _ = provedor(resposta=None)
    with pytest.raises(ErroDoProvedor):
        p.gerar("s", "u", SCHEMA)


def test_conversar_faz_streaming_de_texto_puro():
    p, modelos = provedor(pedacos=["Olá", None, ", <b>mundo</b>"])
    mensagens = [{"papel": "usuario", "texto": "oi"}, {"papel": "modelo", "texto": "olá"},
                 {"papel": "usuario", "texto": "e aí?"}]
    assert list(p.conversar(mensagens, "sistema")) == ["Olá", ", <b>mundo</b>"]
    chamada = modelos.chamadas[0]
    assert [c["role"] for c in chamada["contents"]] == ["user", "model", "user"]
    assert chamada["config"]["system_instruction"] == "sistema"


def test_conversar_429_no_meio_do_stream():
    p, _ = provedor(pedacos=["a", ErroApi(429, corpo_429(retry="5s"))])
    fluxo = p.conversar([{"papel": "usuario", "texto": "oi"}], "s")
    assert next(fluxo) == "a"
    with pytest.raises(ErroDeCota) as erro:
        next(fluxo)
    assert erro.value.espera_s == 5.0


def test_a_chave_nunca_aparece_em_erro_nem_repr():
    casos = [ErroApi(429, corpo_429(retry="1s")),
             ErroApi(400, {"error": {"code": 400, "message": f"API key not valid: {CHAVE}"}}),
             httpx.ConnectError(f"https://x/?key={CHAVE}"),
             RuntimeError(f"falha com {CHAVE}")]
    for falha in casos:
        p, _ = provedor(erro=falha)
        with pytest.raises(ErroDoProvedor) as erro:
            p.gerar("s", "u", SCHEMA)
        # o que um log com traceback imprimiria (o erro original do SDK fica fora: `from None`)
        texto = "".join(traceback.format_exception(erro.value)) + repr(erro.value)
        assert CHAVE not in texto
        assert "AIza" not in texto
    assert CHAVE not in repr(p)


def test_sem_chave_nao_ha_provedor():
    assert criar_provedores("", ["gemini-3.5-flash-lite"]) == []
    falso = SimpleNamespace(models=Modelos(resposta="{}"))
    nomes = [p.nome for p in criar_provedores(CHAVE, ["m1", "m2"], cliente=falso)]
    assert nomes == ["m1", "m2"]


def test_erro_real_do_sdk_e_traduzido():
    errors = pytest.importorskip("google.genai.errors")
    p, _ = provedor(erro=errors.ClientError(429, corpo_429(retry="9s")))
    with pytest.raises(ErroDeCota) as erro:
        p.gerar("s", "u", SCHEMA)
    assert erro.value.espera_s == 9.0
    assert CHAVE not in str(erro.value)
