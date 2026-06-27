#!/usr/bin/env python3
"""
Bot de cotações — texto detalhado + painel com gráficos dos últimos 30 dias.
Dólar, euro, libra, dólar canadense e IBOVESPA.
Envia 1 mensagem de texto + 1 imagem (painel com 5 gráficos) no Telegram.
Fonte: Yahoo Finance (via yfinance) — sem chave, sem cadastro.
"""

import os
import requests
import tempfile
from datetime import datetime
from zoneinfo import ZoneInfo

import yfinance as yf
import matplotlib
matplotlib.use("Agg")  # sem tela (servidor) — obrigatório no GitHub
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

DIAS_MEDIA = 30
FUSO = ZoneInfo("America/Sao_Paulo")

# (código, ticker Yahoo, nome curto, emoji, unidade)
ATIVOS = [
    ("USD", "USDBRL=X", "Dólar",     "💵", "R$ "),
    ("EUR", "EURBRL=X", "Euro",      "💶", "R$ "),
    ("GBP", "GBPBRL=X", "Libra",     "💷", "R$ "),
    ("CAD", "CADBRL=X", "Dólar CAD", "🍁", "R$ "),
    ("BVSP", "^BVSP",   "IBOVESPA",  "📈", ""),
]


def fmt(valor, casas=2):
    """1234.5 -> '1.234,50' (padrão brasileiro)."""
    s = f"{valor:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def seta(pct):
    return "▲" if pct > 0 else ("▼" if pct < 0 else "•")


def fetch_completo(ticker):
    """Retorna dict com dados completos, ou None se falhar."""
    try:
        hist = yf.Ticker(ticker).history(period="50d")
        fech = hist["Close"].dropna()
        if len(fech) < 2:
            return None

        atual = float(fech.iloc[-1])
        anterior = float(fech.iloc[-2])
        pct_dia = (atual - anterior) / anterior * 100

        semana = float(fech.iloc[-6]) if len(fech) >= 6 else None      # ~5 pregões = 1 semana
        pct_semana = ((atual - semana) / semana * 100) if semana else None

        mes_base = float(fech.iloc[-DIAS_MEDIA]) if len(fech) >= DIAS_MEDIA else float(fech.iloc[0])
        pct_mes = (atual - mes_base) / mes_base * 100

        ult30 = fech.tail(DIAS_MEDIA)
        media = float(ult30.mean())
        maxima = float(ult30.max())
        minima = float(ult30.min())
        volat = (maxima - minima) / media * 100

        return {
            "atual": atual, "pct_dia": pct_dia, "pct_semana": pct_semana,
            "pct_mes": pct_mes, "media": media, "maxima": maxima,
            "minima": minima, "volat": volat, "hist": ult30,
        }
    except Exception as e:
        print(f"[aviso] {ticker} indisponivel: {e}")
        return None


def montar_texto(dados):
    agora = datetime.now(FUSO)
    dias = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
    L = [f"📊 *Cotações — {agora:%d/%m} ({dias[agora.weekday()]}) {agora:%H:%M}*\n"]

    for _, ticker, nome, emoji, uni in ATIVOS:
        d = dados.get(ticker)
        if not d:
            L.append(f"{emoji} *{nome}*: dados indisponíveis\n")
            continue
        casas = 0 if uni == "" else 2
        suf = " pts" if uni == "" else ""
        L.append(f"{emoji} *{nome}*")
        L.append(f"  Atual: {uni}{fmt(d['atual'], casas)}{suf}")
        L.append(f"  Hoje: {seta(d['pct_dia'])} {fmt(abs(d['pct_dia']),1)}%")
        if d["pct_semana"] is not None:
            L.append(f"  7 dias: {seta(d['pct_semana'])} {fmt(abs(d['pct_semana']),1)}%")
        L.append(f"  30 dias: {seta(d['pct_mes'])} {fmt(abs(d['pct_mes']),1)}%")
        L.append(f"  Oscilação no mês: {fmt(d['volat'],1)}%")
        L.append(f"  Máx/Mín 30d: {uni}{fmt(d['maxima'],casas)} / {uni}{fmt(d['minima'],casas)}{suf}")
        L.append(f"  Média 30d: {uni}{fmt(d['media'],casas)}{suf}")
        diff = (d["atual"] - d["media"]) / d["media"] * 100
        if diff <= -0.5:
            L.append("  📉 *Abaixo da média* — relativamente barato")
        elif diff >= 0.5:
            L.append("  📈 *Acima da média* — relativamente caro")
        else:
            L.append("  ➡️ *Na média*")
        L.append("")

    L.append("⚠️ _Isto é informação, não recomendação._")
    L.append("_Ninguém prevê o curto prazo — você decide._")
    return "\n".join(L)


def gerar_painel(dados):
    """Gera UMA imagem com os 5 gráficos. Retorna o caminho do PNG ou None."""
    try:
        fig, axes = plt.subplots(3, 2, figsize=(11, 13), dpi=85)
        axes = axes.flatten()

        for i, (_, ticker, nome, _emoji, uni) in enumerate(ATIVOS):
            ax = axes[i]
            d = dados.get(ticker)
            if not d:
                ax.text(0.5, 0.5, f"{nome}\n(sem dados)", ha="center", va="center")
                ax.axis("off")
                continue

            h = d["hist"]
            cor = "#2E86AB"
            ax.plot(h.index, h.values, linewidth=2, color=cor, marker="o", markersize=3)
            # linha da média 30d
            ax.axhline(d["media"], color="#E07A5F", linestyle="--", linewidth=1.3,
                       label=f"Média 30d")
            # ponto atual destacado
            ax.scatter([h.index[-1]], [d["atual"]], color="#C1272D", zorder=5, s=45)

            casas = 0 if uni == "" else 2
            ax.set_title(f"{nome} — {uni}{fmt(d['atual'],casas)}  ({seta(d['pct_dia'])}{fmt(abs(d['pct_dia']),1)}%)",
                         fontsize=12, fontweight="bold")
            ax.grid(True, alpha=0.3, linestyle="--")
            ax.legend(fontsize=8, loc="best")
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
            for lbl in ax.get_xticklabels():
                lbl.set_rotation(45)
                lbl.set_ha("right")
                lbl.set_fontsize(8)

        # esconde o 6º quadro vazio
        axes[5].axis("off")
        agora = datetime.now(FUSO)
        fig.suptitle(f"Cotações — últimos 30 dias ({agora:%d/%m/%Y})",
                     fontsize=15, fontweight="bold", y=0.995)
        fig.tight_layout(rect=[0, 0, 1, 0.98])

        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        fig.savefig(tmp.name, bbox_inches="tight", dpi=85)
        plt.close(fig)
        return tmp.name
    except Exception as e:
        print(f"[aviso] painel falhou: {e}")
        return None


def enviar_telegram(texto, caminho_imagem):
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    # texto
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": texto, "parse_mode": "Markdown"},
        timeout=20,
    )
    if not r.ok:
        print("ERRO do Telegram (texto):", r.status_code, "->", r.text)
    r.raise_for_status()

    # imagem
    if caminho_imagem:
        with open(caminho_imagem, "rb") as f:
            r = requests.post(
                f"https://api.telegram.org/bot{token}/sendPhoto",
                data={"chat_id": chat_id, "caption": "📈 Gráficos dos últimos 30 dias"},
                files={"photo": f},
                timeout=30,
            )
        if not r.ok:
            print("ERRO do Telegram (imagem):", r.status_code, "->", r.text)
        r.raise_for_status()

    print("Mensagem + painel enviados com sucesso.")


def main():
    dados = {ticker: fetch_completo(ticker) for _, ticker, *_ in ATIVOS}
    texto = montar_texto(dados)
    print(texto)
    print("-" * 60)
    imagem = gerar_painel(dados)
    enviar_telegram(texto, imagem)
    if imagem:
        try:
            os.remove(imagem)
        except OSError:
            pass


if __name__ == "__main__":
    main()
