#!/usr/bin/env python3
"""
Bot de cotações - envia dólar, euro, libra, dólar canadense e IBOVESPA no Telegram.
Roda 1x por dia via GitHub Actions. Mostra cotação + variação do dia + comparação
com a média dos últimos 30 dias (sinal objetivo, NÃO recomendação de compra).
"""

import os
import sys
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# --- Configuração -----------------------------------------------------------

MOEDAS = ["USD", "EUR", "GBP", "CAD"]   # pares contra o Real (BRL)
DIAS_MEDIA = 30
FUSO = ZoneInfo("America/Sao_Paulo")

NOMES = {
    "USD": ("DÓLAR", "💵"),
    "EUR": ("EURO",  "💶"),
    "GBP": ("LIBRA", "💷"),
    "CAD": ("CAD",   "🍁"),
}

# --- Formatação de números no padrão brasileiro -----------------------------

def fmt(valor, casas=2):
    """1234.5 -> '1.234,50'  (padrão brasileiro)"""
    s = f"{valor:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

def sinal_media(atual, media):
    """Compara o valor atual com a média de 30 dias."""
    if media is None:
        return ""
    diff = (atual - media) / media * 100
    if diff <= -0.5:
        return f"   📉 abaixo da média de 30d (R$ {fmt(media)}) — relativamente barato"
    elif diff >= 0.5:
        return f"   📈 acima da média de 30d (R$ {fmt(media)}) — relativamente caro"
    else:
        return f"   ➡️ perto da média de 30d (R$ {fmt(media)})"

# --- Coleta de dados: moedas (AwesomeAPI - grátis, sem chave) ----------------

def fetch_moedas():
    """Retorna dict {codigo: {'atual':float,'pct':float,'media':float|None}}."""
    pares = ",".join(f"{m}-BRL" for m in MOEDAS)
    out = {}

    # cotação atual de todas de uma vez
    url = f"https://economia.awesomeapi.com.br/json/last/{pares}"
    dados = requests.get(url, timeout=20).json()

    for m in MOEDAS:
        chave = f"{m}BRL"
        info = dados.get(chave, {})
        atual = float(info.get("bid")) if info.get("bid") else None
        pct = float(info.get("pctChange")) if info.get("pctChange") else None

        # histórico de 30 dias para a média
        media = None
        try:
            h = requests.get(
                f"https://economia.awesomeapi.com.br/json/daily/{m}-BRL/{DIAS_MEDIA}",
                timeout=20,
            ).json()
            bids = [float(d["bid"]) for d in h if d.get("bid")]
            if bids:
                media = sum(bids) / len(bids)
        except Exception as e:
            print(f"[aviso] media {m} indisponivel: {e}")

        out[m] = {"atual": atual, "pct": pct, "media": media}
    return out

# --- Coleta de dados: IBOVESPA (yfinance - grátis, sem chave) ----------------

def fetch_ibovespa():
    """Retorna {'atual':float,'pct':float,'media':float} ou None se falhar."""
    try:
        import yfinance as yf
        hist = yf.Ticker("^BVSP").history(period="45d")
        fechamentos = hist["Close"].dropna()
        if len(fechamentos) < 2:
            return None
        atual = float(fechamentos.iloc[-1])
        anterior = float(fechamentos.iloc[-2])
        pct = (atual - anterior) / anterior * 100
        media = float(fechamentos.tail(DIAS_MEDIA).mean())
        return {"atual": atual, "pct": pct, "media": media}
    except Exception as e:
        print(f"[aviso] ibovespa indisponivel: {e}")
        return None

# --- Montagem da mensagem ----------------------------------------------------

def montar_mensagem(moedas, ibov):
    agora = datetime.now(FUSO)
    dias = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
    cabecalho = f"📊 Cotações — {agora:%d/%m} ({dias[agora.weekday()]}) {agora:%H:%M}"
    linhas = [cabecalho, ""]

    for m in MOEDAS:
        d = moedas.get(m, {})
        nome, emoji = NOMES[m]
        if d.get("atual") is None:
            linhas.append(f"{emoji} {nome}: dados indisponíveis")
            linhas.append("")
            continue
        pct = d.get("pct")
        seta = "▲" if (pct or 0) > 0 else ("▼" if (pct or 0) < 0 else "•")
        pct_txt = f"{seta} {fmt(abs(pct or 0),1)}% hoje" if pct is not None else ""
        linhas.append(f"{emoji} {nome}  R$ {fmt(d['atual'])}  ({pct_txt})")
        s = sinal_media(d["atual"], d.get("media"))
        if s:
            linhas.append(s)
        linhas.append("")

    if ibov:
        seta = "▲" if ibov["pct"] > 0 else ("▼" if ibov["pct"] < 0 else "•")
        linhas.append(f"📈 IBOVESPA  {fmt(ibov['atual'],0)} pts  ({seta} {fmt(abs(ibov['pct']),1)}% hoje)")
        if ibov["atual"] < ibov["media"]:
            linhas.append(f"   📉 abaixo da média de 30d ({fmt(ibov['media'],0)} pts)")
        else:
            linhas.append(f"   📈 acima da média de 30d ({fmt(ibov['media'],0)} pts)")
        linhas.append("")
    else:
        linhas.append("📈 IBOVESPA: dados indisponíveis")
        linhas.append("")

    linhas.append("⚠️ Isto é informação, não recomendação. Ninguém prevê o curto prazo — você decide.")
    return "\n".join(linhas)

# --- Envio pelo Telegram -----------------------------------------------------

def enviar_telegram(texto):
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, json={"chat_id": chat_id, "text": texto}, timeout=20)
    r.raise_for_status()
    print("Mensagem enviada com sucesso.")

# --- Main --------------------------------------------------------------------

def main():
    moedas = fetch_moedas()
    ibov = fetch_ibovespa()
    texto = montar_mensagem(moedas, ibov)
    print(texto)
    print("-" * 40)
    enviar_telegram(texto)

if __name__ == "__main__":
    main()
