"""Manchetes do ativo no Google News RSS (mesma busca do painel, `proxy/noticiasApi.js`).

Usa a rede `saida` do ia-opiniao (TASK-IA-27). Falha de rede devolve lista vazia: manchete e
complemento do pacote, nunca motivo para derrubar o card.
"""

from __future__ import annotations

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET  # noqa: S405 - XML do Google News, sem DTD
from email.utils import parsedate_to_datetime

TIMEOUT_S = 5
LIMITE = 5


def buscar_manchetes(simbolo: str, limite: int = LIMITE) -> list[dict]:
    consulta = urllib.parse.quote(f'"{simbolo}"')
    url = f"https://news.google.com/rss/search?q={consulta}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_S) as resposta:  # noqa: S310 - URL fixa
            raiz = ET.fromstring(resposta.read())  # noqa: S314
    except Exception:  # noqa: BLE001 - rede, HTTP ou XML: sem manchetes
        return []
    saida = []
    for item in raiz.iter("item"):
        titulo, link = (item.findtext("title") or "").strip(), (item.findtext("link") or "").strip()
        if not titulo or not link:
            continue
        publicado = item.findtext("pubDate") or ""
        try:
            publicado = parsedate_to_datetime(publicado).isoformat()
        except (TypeError, ValueError):
            publicado = publicado or None
        saida.append({"titulo": titulo, "link": link, "fonte": (item.findtext("source") or "").strip(),
                      "publicadoEm": publicado})
        if len(saida) >= limite:
            break
    return saida
