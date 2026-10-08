"""Governador de cota do Gemini (SPEC 13.4, TASK-IA-25, DEC-IA-10).

Unica responsabilidade: decidir se uma chamada ao Gemini pode sair agora, contar a que saiu e
guardar respostas repetidas. Nao chama provedor nenhum; a cadeia (TASK-IA-26) pergunta antes.

- Baldes diarios `chat`/`card`/`lote`: percentual do teto diario somado dos modelos (RPD).
  Depois das 18h de America/Sao_Paulo a sobra de um balde serve aos outros.
- Por modelo: limite por minuto (RPM) e teto do dia (RPD) proprios; modelo sem limite conhecido
  usa a reserva (o menor limite do nivel gratuito).
- O dia da cota zera a meia-noite de America/Los_Angeles (quando o Google zera).
- Pausa depois de 429: `retryDelay` da resposta; sem ele 60 s; cota diaria, ate o zeramento.
- Prioridade chat > card > lote: com menos de 15% do teto do dia restante, o lote para.
- Cache de resposta por hash(provedor, modelo, prompt normalizado, schema), valido no dia da cota.

Contagem em SQLite (`/app/var/cota.sqlite` no container); relogio injetavel para os testes.
"""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import threading
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

FUSO_COTA = ZoneInfo("America/Los_Angeles")
FUSO_LOCAL = ZoneInfo("America/Sao_Paulo")
HORA_SOBRA = time(18, 0)
BALDES = ("chat", "card", "lote")
PCT_PADRAO = {"chat": 40, "card": 20, "lote": 40}
CORTE_LOTE = 0.15
PAUSA_PADRAO_S = 60.0
JANELA_RPM_S = 60.0

Relogio = Callable[[], datetime]


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Decisao:
    """Resposta do governador. `motivo`: pausa | rpm | rpd | balde | corte_lote (None quando permitido)."""

    permitido: bool
    motivo: str | None = None
    tentar_apos: datetime | None = None


def _rpm_rpd(limite: Any) -> tuple[int, int]:
    """Aceita (rpm, rpd) ou qualquer objeto com `.rpm`/`.rpd` (ex.: LimiteDeModelo da config)."""
    if isinstance(limite, tuple | list):
        rpm, rpd = limite
    else:
        rpm, rpd = limite.rpm, limite.rpd
    if int(rpm) < 1 or int(rpd) < 1:
        raise ValueError("RPM e RPD precisam ser maiores que zero")
    return int(rpm), int(rpd)


def dia_cota(instante: datetime) -> str:
    """Dia da cota do Google (America/Los_Angeles) em ISO."""
    return instante.astimezone(FUSO_COTA).date().isoformat()


def proximo_zeramento(instante: datetime) -> datetime:
    """Proxima meia-noite de America/Los_Angeles (com horario de verao), em UTC."""
    dia = instante.astimezone(FUSO_COTA).date() + timedelta(days=1)
    return datetime.combine(dia, time(0, 0), tzinfo=FUSO_COTA).astimezone(timezone.utc)


def chave_cache(provedor: str, modelo: str, prompt: str, schema: Mapping | None = None) -> str:
    """Hash estavel: espacos do prompt normalizados e schema com chaves ordenadas."""
    normalizado = " ".join(str(prompt).split())
    bruto = json.dumps([provedor, modelo, normalizado, schema], sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(bruto.encode("utf-8")).hexdigest()


class GovernadorCota:
    def __init__(self, caminho: str | Path, limites: Mapping[str, Any] | Iterable[tuple[str, Any]],
                 pct: Mapping[str, int] | None = None, reserva: Any = (5, 20),
                 agora: Relogio = _agora_utc):
        itens = limites.items() if isinstance(limites, Mapping) else limites
        self._limites = {nome: _rpm_rpd(lim) for nome, lim in itens}
        self._reserva = _rpm_rpd(reserva)
        self._pct = dict(PCT_PADRAO if pct is None else pct)
        if set(self._pct) != set(BALDES) or sum(self._pct.values()) != 100:
            raise ValueError("COTA_*_PCT precisa ter chat, card e lote somando 100")
        self._agora = agora
        self._trava = threading.Lock()
        if str(caminho) != ":memory:":
            Path(caminho).parent.mkdir(parents=True, exist_ok=True)
        self._con = sqlite3.connect(str(caminho), check_same_thread=False, isolation_level=None)
        self._con.executescript("""
            CREATE TABLE IF NOT EXISTS chamada (modelo TEXT NOT NULL, balde TEXT NOT NULL,
                instante REAL NOT NULL, dia TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS ix_chamada_dia ON chamada (dia, modelo);
            CREATE TABLE IF NOT EXISTS pausa (modelo TEXT PRIMARY KEY, ate REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS cache (chave TEXT PRIMARY KEY, valor TEXT NOT NULL, dia TEXT NOT NULL);
        """)

    # --- limites -------------------------------------------------------------------------------

    def limite(self, modelo: str) -> tuple[int, int]:
        return self._limites.get(modelo, self._reserva)

    @property
    def teto_dia(self) -> int:
        """Soma dos RPD dos modelos configurados (padrao 500 + 500 + 20 = 1.020)."""
        return sum(rpd for _, rpd in self._limites.values())

    def teto_balde(self, balde: str) -> int:
        self._balde_valido(balde)
        return self.teto_dia * self._pct[balde] // 100

    @staticmethod
    def _balde_valido(balde: str) -> None:
        if balde not in BALDES:
            raise ValueError(f"balde desconhecido: {balde!r}")

    def _apos_sobra(self, agora: datetime) -> bool:
        return agora.astimezone(FUSO_LOCAL).time() >= HORA_SOBRA

    # --- contagem ------------------------------------------------------------------------------

    def _contar(self, sql: str, *args: Any) -> int:
        return int(self._con.execute(sql, args).fetchone()[0])

    def _usadas(self, dia: str) -> tuple[int, dict[str, int]]:
        por_balde = dict.fromkeys(BALDES, 0)
        for balde, n in self._con.execute("SELECT balde, COUNT(*) FROM chamada WHERE dia = ? GROUP BY balde", (dia,)):
            por_balde[balde] = int(n)
        return sum(por_balde.values()), por_balde

    def _disponivel_balde(self, balde: str, agora: datetime) -> int:
        """Quantas chamadas o balde ainda pode fazer hoje (sem olhar os limites dos modelos)."""
        total, por_balde = self._usadas(dia_cota(agora))
        restante_total = max(0, self.teto_dia - total)
        if self._apos_sobra(agora):
            disponivel = restante_total
        else:
            disponivel = min(max(0, self.teto_balde(balde) - por_balde[balde]), restante_total)
        if balde == "lote":
            limiar = CORTE_LOTE * self.teto_dia
            # chamada k (0, 1, ...) sai enquanto restante_total - k >= limiar
            disponivel = min(disponivel, math.floor(restante_total - limiar) + 1 if restante_total >= limiar else 0)
        return max(0, disponivel)

    def reservar(self, balde: str, modelo: str) -> Decisao:
        """Confere pausa, RPM, RPD, balde e corte do lote; se tudo passa, conta a chamada e permite."""
        self._balde_valido(balde)
        with self._trava:
            agora = self._agora()
            dia = dia_cota(agora)
            ts = agora.timestamp()
            self._con.execute("BEGIN IMMEDIATE")
            try:
                decisao = self._decidir(balde, modelo, agora, dia, ts)
                if decisao.permitido:
                    self._con.execute("INSERT INTO chamada (modelo, balde, instante, dia) VALUES (?, ?, ?, ?)",
                                      (modelo, balde, ts, dia))
                self._con.execute("DELETE FROM chamada WHERE dia < ?", (dia,))
                self._con.execute("COMMIT")
            except BaseException:
                self._con.execute("ROLLBACK")
                raise
            return decisao

    def _decidir(self, balde: str, modelo: str, agora: datetime, dia: str, ts: float) -> Decisao:
        linha = self._con.execute("SELECT ate FROM pausa WHERE modelo = ?", (modelo,)).fetchone()
        if linha and linha[0] > ts:
            return Decisao(False, "pausa", datetime.fromtimestamp(linha[0], timezone.utc))

        rpm, rpd = self.limite(modelo)
        if self._contar("SELECT COUNT(*) FROM chamada WHERE modelo = ? AND dia = ?", modelo, dia) >= rpd:
            return Decisao(False, "rpd", proximo_zeramento(agora))
        janela = self._con.execute(
            "SELECT instante FROM chamada WHERE modelo = ? AND instante > ? ORDER BY instante",
            (modelo, ts - JANELA_RPM_S)).fetchall()
        if len(janela) >= rpm:
            return Decisao(False, "rpm", datetime.fromtimestamp(janela[0][0] + JANELA_RPM_S, timezone.utc))

        if self._disponivel_balde(balde, agora) <= 0:
            total, por_balde = self._usadas(dia)
            if balde == "lote" and self.teto_dia - total < CORTE_LOTE * self.teto_dia:
                return Decisao(False, "corte_lote", proximo_zeramento(agora))
            sobra = datetime.combine(agora.astimezone(FUSO_LOCAL).date(), HORA_SOBRA, tzinfo=FUSO_LOCAL)
            espera = sobra if not self._apos_sobra(agora) and total < self.teto_dia else proximo_zeramento(agora)
            return Decisao(False, "balde", espera.astimezone(timezone.utc))
        return Decisao(True)

    # --- pausa ---------------------------------------------------------------------------------

    def pausar(self, modelo: str, espera_s: float | None = None, diaria: bool = False) -> datetime:
        """Pausa o modelo depois de um 429. Nunca encurta uma pausa ja maior."""
        with self._trava:
            agora = self._agora()
            if diaria:
                ate = proximo_zeramento(agora)
            else:
                ate = agora + timedelta(seconds=PAUSA_PADRAO_S if espera_s is None else max(0.0, espera_s))
            self._con.execute(
                "INSERT INTO pausa (modelo, ate) VALUES (?, ?) "
                "ON CONFLICT(modelo) DO UPDATE SET ate = MAX(ate, excluded.ate)",
                (modelo, ate.timestamp()))
            ate_gravado = self._con.execute("SELECT ate FROM pausa WHERE modelo = ?", (modelo,)).fetchone()[0]
            return datetime.fromtimestamp(ate_gravado, timezone.utc)

    # --- leitura para /saude e respostas --------------------------------------------------------

    def restante(self, balde: str) -> int:
        self._balde_valido(balde)
        with self._trava:
            return self._disponivel_balde(balde, self._agora())

    def gemini_disponivel(self, balde: str) -> bool:
        """Algum modelo pode atender este balde agora (sem contar a chamada)."""
        with self._trava:
            agora = self._agora()
            if self._disponivel_balde(balde, agora) <= 0:
                return False
            dia, ts = dia_cota(agora), agora.timestamp()
            return any(self._decidir(balde, m, agora, dia, ts).permitido for m in self._limites)

    def estado_modelos(self) -> list[dict]:
        """Bloco `provedores.gemini.modelos` do /saude (13.3)."""
        with self._trava:
            agora = self._agora()
            dia, ts = dia_cota(agora), agora.timestamp()
            estado = []
            for nome, (_, rpd) in self._limites.items():
                pausa = self._con.execute("SELECT ate FROM pausa WHERE modelo = ?", (nome,)).fetchone()
                em_pausa = (datetime.fromtimestamp(pausa[0], timezone.utc).isoformat()
                            if pausa and pausa[0] > ts else None)
                usadas = self._contar("SELECT COUNT(*) FROM chamada WHERE modelo = ? AND dia = ?", nome, dia)
                estado.append({"nome": nome, "em_pausa_ate": em_pausa, "usadas_hoje": usadas, "teto_dia": rpd})
            return estado

    # --- cache ---------------------------------------------------------------------------------

    def cache_obter(self, chave: str) -> str | None:
        with self._trava:
            linha = self._con.execute("SELECT valor, dia FROM cache WHERE chave = ?", (chave,)).fetchone()
            if linha and linha[1] == dia_cota(self._agora()):
                return linha[0]
            return None

    def cache_gravar(self, chave: str, valor: str) -> None:
        with self._trava:
            dia = dia_cota(self._agora())
            self._con.execute("INSERT OR REPLACE INTO cache (chave, valor, dia) VALUES (?, ?, ?)", (chave, valor, dia))
            self._con.execute("DELETE FROM cache WHERE dia < ?", (dia,))

    def fechar(self) -> None:
        self._con.close()
