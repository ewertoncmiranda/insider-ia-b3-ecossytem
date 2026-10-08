"""TASK-IA-34: testes das guardas do chat."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.chat.guardas import (
    CodigoErro,
    LimiteAtingido,
    classificar_tema,
    contem_vocab_proibido,
    detectar_numeros_sem_fonte,
    verificar_limites,
)


# ---------------------------------------------------------------------------
# classificar_tema
# ---------------------------------------------------------------------------

def test_receita_de_bolo_fora_do_tema():
    assert classificar_tema("receita de bolo de chocolate com 3 xícaras de farinha") == CodigoErro.FORA_DO_TEMA


def test_ticker_passa():
    assert classificar_tema("o que aconteceu com PETR4 hoje?") is None


def test_devo_comprar_passa():
    # "devo comprar" sem ticker → deve tentar o sistema de finanças
    # Com ticker claramente financeiro
    assert classificar_tema("devo comprar VALE3 agora?") is None


def test_futebol_fora_do_tema():
    assert classificar_tema("qual time vai ganhar a copa do Brasil de futebol esta temporada?") == CodigoErro.FORA_DO_TEMA


def test_pergunta_financeira_passa():
    assert classificar_tema("qual é o P/L de ITUB4 hoje?") is None


def test_pergunta_sobre_bolsa_passa():
    assert classificar_tema("como funciona o ibovespa?") is None


def test_pergunta_curta_sem_pista_passa():
    # Mensagem curta (≤6 palavras) sem pista → aceitar
    assert classificar_tema("o que é ROE?") is None


# ---------------------------------------------------------------------------
# verificar_limites
# ---------------------------------------------------------------------------

class FakeSessoes:
    def __init__(self, total_hoje: int = 0, ultima: float | None = None):
        self._total = total_hoje
        self._ultima = ultima

    def total_hoje(self, sid): return self._total
    def ultima_mensagem_usuario(self, sid): return self._ultima


def _agora():
    return datetime.now(timezone.utc)


def test_limite_diario_atingido():
    sessoes = FakeSessoes(total_hoje=60)
    with pytest.raises(LimiteAtingido) as exc:
        verificar_limites("s1", sessoes, max_dia=60, intervalo_s=3)
    assert exc.value.codigo == CodigoErro.LIMITE
    assert "60" in str(exc.value)


def test_limite_diario_nao_atingido():
    sessoes = FakeSessoes(total_hoje=59)
    verificar_limites("s1", sessoes, max_dia=60, intervalo_s=3)  # não deve lançar


def test_intervalo_muito_curto():
    import time
    ts_recente = time.time() - 1  # 1 segundo atrás
    sessoes = FakeSessoes(ultima=ts_recente)
    with pytest.raises(LimiteAtingido) as exc:
        verificar_limites("s1", sessoes, max_dia=60, intervalo_s=3)
    assert exc.value.codigo == CodigoErro.LIMITE


def test_intervalo_ok():
    import time
    ts_antigo = time.time() - 5  # 5 segundos atrás
    sessoes = FakeSessoes(ultima=ts_antigo)
    verificar_limites("s1", sessoes, max_dia=60, intervalo_s=3)  # não deve lançar


def test_sem_historico_passa():
    sessoes = FakeSessoes(total_hoje=0, ultima=None)
    verificar_limites("s1", sessoes, max_dia=60, intervalo_s=3)  # não deve lançar


# ---------------------------------------------------------------------------
# detectar_numeros_sem_fonte
# ---------------------------------------------------------------------------

def test_numero_sem_fonte_detectado():
    texto = "O ativo cresceu 12,4% no último trimestre."
    numeros = detectar_numeros_sem_fonte(texto)
    assert len(numeros) > 0


def test_numero_com_indicador_de_fonte_ignorado():
    texto = "Segundo o balanço, o ROE foi 12,4%."
    numeros = detectar_numeros_sem_fonte(texto)
    assert len(numeros) == 0


def test_texto_sem_numero_retorna_vazio():
    texto = "O mercado está volátil hoje."
    assert detectar_numeros_sem_fonte(texto) == []


# ---------------------------------------------------------------------------
# contem_vocab_proibido
# ---------------------------------------------------------------------------

def test_vocab_proibido_invista():
    assert contem_vocab_proibido("Invista agora enquanto o preço está baixo!")


def test_vocab_proibido_garanto():
    assert contem_vocab_proibido("Garanto que vai subir essa semana.")


def test_vocab_proibido_compre():
    assert contem_vocab_proibido("Compre PETR4 agora, não vai se arrepender.")


def test_sem_vocab_proibido():
    assert not contem_vocab_proibido(
        "O ativo apresentou P/L de 18 e ROE de 21%. "
        "Esta é uma leitura automática dos números."
    )


def test_leitura_neutra_sem_vocab_proibido():
    assert not contem_vocab_proibido(
        "PETR4 fechou em R$ 38,50 com variação de +0,8% no dia."
    )
