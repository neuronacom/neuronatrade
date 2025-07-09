import os
import requests
from flask import Flask, jsonify
from flask_cors import CORS
import openai

BINANCE_TICKER = "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"
BINANCE_ORDERBOOK = "https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=100"
CRYPTOPANIC_NEWS = "https://cryptopanic.com/api/v1/posts/?auth_token=" + os.getenv("CRYPTOPANIC_API_KEY") + "&currencies=BTC&filter=important"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app)
openai.api_key = OPENAI_API_KEY

def fetch_binance_signal():
    # Получаем цену и объёмы
    ticker = requests.get(BINANCE_TICKER).json()
    orderbook = requests.get(BINANCE_ORDERBOOK).json()
    price = float(ticker.get("lastPrice", 0))
    buy_vol = sum(float(b[1]) for b in orderbook["bids"])
    sell_vol = sum(float(a[1]) for a in orderbook["asks"])
    change = float(ticker.get("priceChangePercent", 0))

    # Simple logic for entry/SL/TP
    entry = price
    sl = round(price * 0.985, 2)
    tp_min = round(price * 1.008, 2)
    tp_max = round(price * 1.025, 2)
    signal_type = "LONG" if buy_vol > sell_vol else "SHORT"
    color = "green" if signal_type == "LONG" else "red"

    # Придумываем сигнал (здесь можно усложнить логику)
    return {
        "symbol": "BTC/USDT",
        "type": signal_type,
        "entry": round(entry, 2),
        "sl": sl,
        "tp": f"{tp_min} — {tp_max}",
        "change": change,
        "color": color,
        "buy_vol": round(buy_vol, 2),
        "sell_vol": round(sell_vol, 2)
    }

def fetch_cryptopanic_news():
    r = requests.get(CRYPTOPANIC_NEWS)
    js = r.json()
    news = []
    for post in js.get("results", []):
        news.append({
            "title": post["title"],
            "url": post["url"],
            "time": post.get("published_at", ""),
        })
    return news

def ai_comment(signal, news):
    if not OPENAI_API_KEY:
        return ""
    try:
        prompt = f"""Ты топовый крипто-трейдер. Сигнал по BTC/USDT:
Сигнал: {signal['type']}
Вход: {signal['entry']}
TP: {signal['tp']}
SL: {signal['sl']}
24ч Изменение: {signal['change']}%
Объём BID: {signal['buy_vol']}, ASK: {signal['sell_vol']}
Последняя новость: {news[0]['title'] if news else ''}

Дай лаконичный профессиональный комментарий: как торговать, что учесть, почему так, стоит ли рисковать."""
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120,
            temperature=0.8,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI error: {e}"

@app.route("/api/feed")
def api_feed():
    try:
        signal = fetch_binance_signal()
        news = fetch_cryptopanic_news()
        comment = ai_comment(signal, news)
        return jsonify({
            "signal": signal,
            "news": news,
            "ai_comment": comment
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
