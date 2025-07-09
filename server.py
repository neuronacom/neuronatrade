import os
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY")
CRYPTOPANIC_API_KEY = os.environ.get("CRYPTOPANIC_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

def fetch_btc_signal():
    ticker = requests.get("https://api.binance.com/api/v3/ticker/bookTicker?symbol=BTCUSDT").json()
    price = float(ticker['bidPrice'])
    if price > 60000:
        return {
            "type": "signal",
            "text": f"<b>BTC/USDT LONG</b> (Объёмы растут)\nВход: <b>{int(price)}</b><br>Тейк: <b>{int(price*1.01)}</b><br>Стоп: <b>{int(price*0.995)}</b>"
        }
    else:
        return {
            "type": "signal",
            "text": f"<b>BTC/USDT SHORT</b> (Объёмы падают)\nВход: <b>{int(price)}</b><br>Тейк: <b>{int(price*0.985)}</b><br>Стоп: <b>{int(price*1.006)}</b>"
        }

def fetch_news():
    url = f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTOPANIC_API_KEY}&currencies=BTC&filter=important"
    news = []
    try:
        resp = requests.get(url).json()
        for n in resp.get('results', [])[:3]:
            news.append({
                "type": "news",
                "text": f"📰 <b>{n.get('title','')}</b> <a href='{n.get('url','')}' target='_blank'>Источник</a>"
            })
    except Exception as e:
        pass
    return news

@app.route("/api/feed")
def api_feed():
    result = []
    result.append(fetch_btc_signal())
    result += fetch_news()
    return jsonify({"messages": result})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
