#!/usr/bin/env python3
"""
Bot de cotações - dólar, euro, libra, dólar canadense e IBOVESPA no Telegram.
Roda 1x por dia via GitHub Actions. Mostra cotação + variação do dia + comparação
com a média dos últimos 30 dias (sinal objetivo, NÃO recomendação de compra).
Fonte única: Yahoo Finance (via yfinance) — sem chave, sem cadastro.
"""

import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import yfinance as yf

DIAS_MEDIA = 30
FUSO = ZoneInfo("America/Sao_Paulo")

# (código, ticker no Yahoo, nome, emoji)
ATIVOS = [
    ("USD", "USDBRL=X", "DÓLAR", "💵"),
    ("EUR", "EURBRL=X", "EURO",  "💶"),
    ("GBP", "GBPBRL=X", "LIBRA", "💷"),
    ("CAD", "CADBRL=X", "CAD",   "🍁"),
]
IBOV_TICKER = "^BVSP"


def fmt(valor, casas=2):
    """1234.5 -> '1.234,50' (padrão brasileiro)."""
    s = f"{valor:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def seta(pct):
    return "▲" if pct > 0 else ("▼" if pct < 0 else "•")


def fetch_ticker(ticker):
    """Retorna (atual, pct_do_dia, media30) ou (None, None, None) se falhar."""
    try:
        hist = yf.Ticker(ticker).history(period="45d")
        fech = hist["Close"].dropna()
        if len(fech) < 2:
            return None, None, None
        atual = float(fech.iloc[-1])
        anterior = float(fech.iloc[-2])
        pct = (atual - anterior) / anterior * 100
        media = float(fech.tail(DIAS_MEDIA).mean())
        return atual, pct, media
    except Exception as e:
        print(f"[aviso] {ticker} indisponivel: {e}")
        return None, None, None


def sinal_media(atual, media):
    if media is None:
        return ""
    diff = (atual - media) / media * 100
    if diff <= -0.5:
        return f"   📉 abaixo da média de 30d (R$ {fmt(media)}) — relativamente barato"
    elif diff >= 0.5:
        return f"   📈 acima da média de 30d (R$ {fmt(media)}) — relativamente caro"
    return f"   ➡️ perto da média de 30d (R$ {fmt(media)})"


def montar_mensagem():
    agora = datetime.now(FUSO)
    dias = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
    linhas = [f"📊 Cotações — {agora:%d/%m} ({dias[agora.weekday()]}) {agora:%H:%M}", ""]

    for _, ticker, nome, emoji in ATIVOS:
        atual, pct, media = fetch_ticker(ticker)
        if atual is None:
            linhas += [f"{emoji} {nome}: dados indisponíveis", ""]
            continue
        linhas.append(f"{emoji} {nome}  R$ {fmt(atual)}  ({seta(pct)} {fmt(abs(pct),1)}% hoje)")
        s = sinal_media(atual, media)
        if s:
            linhas.append(s)
        linhas.append("")

    atual, pct, media = fetch_ticker(IBOV_TICKER)
    if atual is None:
        linhas += ["📈 IBOVESPA: dados indisponíveis", ""]
    else:
        linhas.append(f"📈 IBOVESPA  {fmt(atual,0)} pts  ({seta(pct)} {fmt(abs(pct),1)}% hoje)")
        if media is not None:
            if atual < media:
                linhas.append(f"   📉 abaixo da média de 30d ({fmt(media,0)} pts)")
            else:
                linhas.append(f"   📈 acima da média de 30d ({fmt(media,0)} pts)")
        linhas.append("")

    linhas.append("⚠️ Isto é informação, não recomendação. Ninguém prevê o curto prazo — você decide.")
    return "\n".join(linhas)


def enviar_telegram(texto):
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, json={"chat_id": chat_id, "text": texto}, timeout=20)
    if not r.ok:
        # mostra o motivo EXATO do Telegram no log (ajuda a diagnosticar)
        print("ERRO do Telegram:", r.status_code, "->", r.text)
    r.raise_for_status()
    print("Mensagem enviada com sucesso.")


def main():
    texto = montar_mensagem()
    print(texto)
    print("-" * 40)
    enviar_telegram(texto)


if __name__ == "__main__":
    main()
