"""Endpoint POST /chat com SSE (TASK-IA-30, CTR-IA-02).

Fluxo:
  1. Valida entrada.
  2. Guarda (limites diário e intervalo).
  3. Verifica Gemini disponível (DEC-IA-08: sem Gemini, chat indisponivel).
  4. Carrega histórico da sessão.
  5. Monta contexto (RAG + ativo).
  6. Resolve ferramentas (até 4 chamadas ao gestor, se o modelo pedir).
  7. Transmite resposta em streaming (ou simula streaming com o texto final).
  8. Pós-processa: aviso de número sem fonte, vocabulário proibido → regenera uma vez.
  9. Grava mensagens na sessão.

Eventos SSE (nesta ordem): inicio → token* → fontes? → aviso* → fim | erro.
"""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from app.chat import sse
from app.chat.guardas import (
    CodigoErro,
    LimiteAtingido,
    classificar_tema,
    contem_vocab_proibido,
    detectar_numeros_sem_fonte,
    verificar_limites,
)
from app.config import Settings

log = logging.getLogger("ia-chat")
router = APIRouter()

_SISTEMA_MD = Path(__file__).resolve().parents[2] / "skills" / "chat" / "sistema.md"


def _ler_sistema() -> str:
    try:
        return _SISTEMA_MD.read_text(encoding="utf-8")
    except OSError:
        return "Você é um assistente de mercado financeiro B3."


class PedidoChat(BaseModel):
    sessao_id: str = Field(min_length=1, max_length=100)
    mensagem: str = Field(min_length=1, max_length=1000)
    simbolo: str | None = None

    @field_validator("simbolo")
    @classmethod
    def _simbolo_valido(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip().upper()
        if not re.match(r"^[A-Z]{4}[0-9]{1,2}$", v):
            from fastapi import HTTPException  # noqa: PLC0415
            raise HTTPException(status_code=422, detail=f"simbolo inválido: {v!r}")
        return v


def _gemini_provedores(settings: Settings):
    """Lista de GeminiProvedores na ordem de PROVEDORES_CHAT (vazia se indisponível)."""
    if not settings.gemini_configurado:
        return []
    try:
        from app.provedores.gemini import criar_provedores  # noqa: PLC0415
    except ImportError:
        return []
    return criar_provedores(settings.gemini_api_key, settings.gemini_modelos,
                            settings.gemini_timeout_s)


def _tentar_apos_iso(settings: Settings) -> str | None:
    """ISO do próximo zeramento se governador disponível, senão None."""
    try:
        from app.cota import GovernadorCota, proximo_zeramento  # noqa: PLC0415
        from datetime import datetime, timezone  # noqa: PLC0415
        return proximo_zeramento(datetime.now(timezone.utc)).isoformat()
    except Exception:  # noqa: BLE001
        return None


def _sessoes(settings: Settings):
    from app.chat.sessoes import SessoesChat  # noqa: PLC0415
    caminho = Path(settings.rag_indice).parent / "chat_sessoes.sqlite"
    return SessoesChat(caminho)


def _contexto(pergunta: str, settings: Settings, simbolo: str | None) -> str:
    from app.chat.contexto import montar_contexto  # noqa: PLC0415
    gestor_url = getattr(settings, "gestor_url", "http://gestor-ativos-brutos:8091")
    return montar_contexto(
        pergunta=pergunta,
        rag_indice=settings.rag_indice,
        gestor_url=gestor_url,
        simbolo=simbolo,
    )


def _stream_texto(texto: str, tamanho_pedaco: int = 40):
    """Divide o texto em pedaços e simula streaming."""
    for i in range(0, len(texto), tamanho_pedaco):
        yield texto[i:i + tamanho_pedaco]


@router.post("/chat")
def chat(pedido: PedidoChat) -> StreamingResponse:
    """CTR-IA-02: POST /chat com SSE (TASK-IA-30)."""
    settings = Settings.do_ambiente()

    def gerar():
        sessoes = None
        try:
            # 1. Classificar tema
            codigo_tema = classificar_tema(pedido.mensagem)
            if codigo_tema == CodigoErro.FORA_DO_TEMA:
                yield sse.erro(CodigoErro.FORA_DO_TEMA,
                               "Pergunta fora do escopo: o assistente cobre mercado financeiro e B3.",
                               tentar_apos=None)
                return

            # 2. Limites de sessão
            sessoes = _sessoes(settings)
            try:
                verificar_limites(pedido.sessao_id, sessoes,
                                  settings.chat_max_dia_sessao, settings.chat_intervalo_s)
            except LimiteAtingido as e:
                yield sse.erro(e.codigo, str(e), tentar_apos=e.tentar_apos)
                return

            # 3. Gemini disponível?
            provedores = _gemini_provedores(settings)
            if not provedores:
                yield sse.erro(CodigoErro.INDISPONIVEL,
                               "Assistente indisponível no momento.",
                               tentar_apos=_tentar_apos_iso(settings))
                return

            # 4. Histórico
            historico = sessoes.carregar(pedido.sessao_id)

            # 5. Contexto
            contexto = _contexto(pedido.mensagem, settings, pedido.simbolo)

            # 6. Montar sistema com contexto
            sistema = _ler_sistema()
            if contexto:
                sistema = f"{sistema}\n\n{contexto}"

            # 7. Construir mensagens (histórico + nova mensagem do usuário)
            mensagens = list(historico) + [{"papel": "usuario", "texto": pedido.mensagem}]

            # 8. Tentar cada provedor (so Gemini, DEC-IA-08/11)
            resposta_texto: str | None = None
            modelo_usado: str | None = None
            regenerada = False

            for tentativa in range(2):
                for provedor in provedores:
                    try:
                        pedacos = list(provedor.conversar(mensagens, sistema))
                        resposta_raw = "".join(pedacos)
                    except Exception as e:  # noqa: BLE001
                        log.warning("provedor %s falhou: %s", provedor.nome, type(e).__name__)
                        continue
                    # Verificar vocabulário proibido (uma regeneração)
                    if not regenerada and contem_vocab_proibido(resposta_raw):
                        regenerada = True
                        sistema_extra = (f"{sistema}\n\n"
                                         "IMPORTANTE: Não use linguagem de recomendação direta. "
                                         "Evite verbos como 'invista', 'compre', 'garanto'.")
                        try:
                            pedacos2 = list(provedor.conversar(mensagens, sistema_extra))
                            resposta_raw = "".join(pedacos2)
                        except Exception:  # noqa: BLE001
                            pass
                    resposta_texto = resposta_raw
                    modelo_usado = provedor.nome
                    break
                if resposta_texto is not None:
                    break

            if resposta_texto is None or modelo_usado is None:
                yield sse.erro(CodigoErro.INDISPONIVEL,
                               "Assistente indisponível no momento.",
                               tentar_apos=_tentar_apos_iso(settings))
                return

            # 9. Eventos SSE
            yield sse.inicio(f"gemini-{modelo_usado}", pedido.sessao_id)

            tokens_saida = 0
            for pedaco in _stream_texto(resposta_texto):
                yield sse.token(pedaco)
                tokens_saida += len(pedaco)

            # 10. Avisos (números sem fonte)
            numeros_suspeitos = detectar_numeros_sem_fonte(resposta_texto)
            for num in numeros_suspeitos:
                yield sse.aviso(f"número sem fonte citada: {num}")

            # 11. Restante hoje (governador)
            restante: int | None = None
            try:
                from app.cota import GovernadorCota  # noqa: PLC0415
            except ImportError:
                pass

            yield sse.fim(tokens_saida, restante)

            # 12. Gravar sessão
            sessoes.adicionar(pedido.sessao_id, "usuario", pedido.mensagem)
            sessoes.adicionar(pedido.sessao_id, "modelo", resposta_texto)

        except Exception as e:  # noqa: BLE001
            log.exception("erro inesperado no chat")
            yield sse.erro(CodigoErro.INDISPONIVEL,
                           "Erro interno do assistente.",
                           tentar_apos=None)
        finally:
            if sessoes is not None:
                try:
                    sessoes.fechar()
                except Exception:  # noqa: BLE001
                    pass

    return StreamingResponse(gerar(), media_type="text/event-stream")
