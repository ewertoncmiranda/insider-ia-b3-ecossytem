"""Sessões do chat em SQLite (TASK-IA-31, SPEC GEM-4).

- Últimas 12 mensagens por sessão (janela do modelo).
- Expiração: 24 h a partir da primeira mensagem da sessão.
- A cada 8 mensagens acumuladas (total, não janela) o bloco mais antigo é
  resumido em uma única mensagem "resumo" via o provedor (balde `chat`).
  Assim a janela nunca cresce além de 12: resumo + novas mensagens.
- Relógio injetável para os testes.
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Protocol

JANELA_MENSAGENS = 12
TAMANHO_RESUMO = 8
EXPIRACAO_H = 24


class ProvedorResumo(Protocol):
    def gerar(self, sistema: str, usuario: str, schema: dict) -> str: ...


Relogio = Callable[[], datetime]


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


def _esquema() -> str:
    return """
        CREATE TABLE IF NOT EXISTS mensagem (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            sessao   TEXT    NOT NULL,
            papel    TEXT    NOT NULL,
            texto    TEXT    NOT NULL,
            criado   REAL    NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_msg_sessao ON mensagem (sessao, criado);
    """


class SessoesChat:
    def __init__(self, caminho: str | Path, agora: Relogio = _agora_utc):
        self._agora = agora
        self._trava = threading.Lock()
        if str(caminho) != ":memory:":
            Path(caminho).parent.mkdir(parents=True, exist_ok=True)
        self._con = sqlite3.connect(str(caminho), check_same_thread=False, isolation_level=None)
        self._con.executescript(_esquema())

    def _ts(self) -> float:
        return self._agora().timestamp()

    def _expiracao(self, sessao: str) -> float | None:
        """Timestamp de criação da primeira mensagem da sessão; None se inexistente."""
        linha = self._con.execute(
            "SELECT MIN(criado) FROM mensagem WHERE sessao = ?", (sessao,)
        ).fetchone()
        return linha[0] if linha and linha[0] is not None else None

    def expirado(self, sessao: str) -> bool:
        primeira = self._expiracao(sessao)
        if primeira is None:
            return False
        limite = primeira + EXPIRACAO_H * 3600
        return self._ts() > limite

    def _limpar_expiradas(self) -> None:
        limite = self._ts() - EXPIRACAO_H * 3600
        self._con.execute("DELETE FROM mensagem WHERE sessao IN ("
                          "  SELECT DISTINCT sessao FROM mensagem "
                          "  GROUP BY sessao HAVING MIN(criado) < ?)", (limite,))

    def total_hoje(self, sessao: str) -> int:
        """Número de mensagens do usuário na sessão (24 h), para os limites de CHAT_MAX_DIA_SESSAO."""
        inicio = self._ts() - EXPIRACAO_H * 3600
        return int(self._con.execute(
            "SELECT COUNT(*) FROM mensagem WHERE sessao = ? AND papel = 'usuario' AND criado >= ?",
            (sessao, inicio)).fetchone()[0])

    def ultima_mensagem_usuario(self, sessao: str) -> float | None:
        """Timestamp da última mensagem do usuário (para checar CHAT_INTERVALO_S)."""
        linha = self._con.execute(
            "SELECT MAX(criado) FROM mensagem WHERE sessao = ? AND papel = 'usuario'", (sessao,)
        ).fetchone()
        return linha[0] if linha and linha[0] is not None else None

    def carregar(self, sessao: str) -> list[dict]:
        """Últimas JANELA_MENSAGENS mensagens (modelo usa como histórico)."""
        linhas = self._con.execute(
            "SELECT papel, texto FROM mensagem WHERE sessao = ? ORDER BY criado DESC LIMIT ?",
            (sessao, JANELA_MENSAGENS)).fetchall()
        return [{"papel": papel, "texto": texto} for papel, texto in reversed(linhas)]

    def adicionar(self, sessao: str, papel: str, texto: str) -> None:
        with self._trava:
            self._con.execute(
                "INSERT INTO mensagem (sessao, papel, texto, criado) VALUES (?, ?, ?, ?)",
                (sessao, papel, texto, self._ts()))
            self._limpar_expiradas()

    def total_acumulado(self, sessao: str) -> int:
        return int(self._con.execute(
            "SELECT COUNT(*) FROM mensagem WHERE sessao = ?", (sessao,)).fetchone()[0])

    def precisa_resumir(self, sessao: str) -> bool:
        """Verdadeiro quando atingiu múltiplo de TAMANHO_RESUMO após a última sumarização."""
        total = self.total_acumulado(sessao)
        if total < TAMANHO_RESUMO:
            return False
        tem_resumo = self._con.execute(
            "SELECT COUNT(*) FROM mensagem WHERE sessao = ? AND papel = 'resumo'", (sessao,)
        ).fetchone()[0]
        mensagens_desde = total - int(tem_resumo) * TAMANHO_RESUMO
        return mensagens_desde >= TAMANHO_RESUMO

    def resumir(self, sessao: str, provedor: ProvedorResumo) -> None:
        """Comprime as mensagens mais antigas (exceto as últimas 4) num único 'resumo'."""
        todas = self._con.execute(
            "SELECT id, papel, texto FROM mensagem WHERE sessao = ? ORDER BY criado", (sessao,)
        ).fetchall()
        if len(todas) <= 4:
            return
        para_resumir = todas[:-4]
        historico = "\n".join(f"{papel}: {texto}" for _, papel, texto in para_resumir)
        sistema = (
            "Você é um assistente que comprime histórico de conversas sobre mercado financeiro. "
            "Resuma o histórico a seguir em português em no máximo 200 palavras, "
            "preservando fatos numéricos e tickers mencionados."
        )
        try:
            resumo_texto = provedor.gerar(sistema, historico, {"type": "string"})
        except Exception:  # noqa: BLE001
            return
        ids = [str(row[0]) for row in para_resumir]
        ts = self._ts()
        with self._trava:
            self._con.execute(f"DELETE FROM mensagem WHERE id IN ({','.join(ids)})")
            self._con.execute(
                "INSERT INTO mensagem (sessao, papel, texto, criado) VALUES (?, 'resumo', ?, ?)",
                (sessao, resumo_texto, ts))

    def fechar(self) -> None:
        self._con.close()
