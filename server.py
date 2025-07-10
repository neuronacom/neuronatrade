import os
import requests
from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
import openai

app = Flask(__name__, static_folder='static')
CORS(app)

BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY", "")
BINANCE_SECRET = os.environ.get("BINANCE_SECRET", "")
CRYPTOPANIC_API_KEY = os.environ.get("CRYPTOPANIC_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

openai.api_key = OPENAI_API_KEY

def get_binance_btc_data():
    base_url = "https://api.binance.com"
    depth = requests.get(f"{base_url}/api/v3/depth?symbol=BTCUSDT&limit=10").json()
    ticker = requests.get(f"{base_url}/api/v3/ticker/24hr?symbol=BTCUSDT").json()
    return {
        "bids": depth.get("bids", []),
        "asks": depth.get("asks", []),
        "lastPrice": ticker.get("lastPrice"),
        "volume": ticker.get("volume"),
        "priceChangePercent": ticker.get("priceChangePercent")
    }

def get_cryptopanic_news():
    url = f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTOPANIC_API_KEY}&currencies=BTC&public=true"
    news = requests.get(url).json()
    return [{"title": n['title'], "url": n['url'], "published_at": n["published_at"]} for n in news.get('results', [])[:3]]

def ai_btc_signal(data, news):
    messages = [
        {"role": "system", "content": "Ты профессиональный трейдер криптовалют. Дай краткий анализ BTC/USDT на основе стакана, объёмов, новостей и индикаторов (RSI, MA, MACD, OBV, OrderBook). Твои сигналы: LONG, SHORT, HOLD. Пример ответа: 'Сигнал: LONG от 58900, SL 58000, TP 60000. Комментарий: ...'"},
        {"role": "user", "content": f"Данные Binance: {data}\nНовости: {news}"}
    ]
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=350
    )
    return response.choices[0].message.content.strip()

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/index.html")
def index2():
    return send_from_directory(".", "index.html")

@app.route("/static/<path:path>")
def static_files(path):
    return send_from_directory("static", path)

@app.route("/api/data")
def api_data():
    btc = get_binance_btc_data()
    news = get_cryptopanic_news()
    return jsonify({"btc": btc, "news": news})

@app.route("/api/signal")
def api_signal():
    btc = get_binance_btc_data()
    news = get_cryptopanic_news()
    signal = ai_btc_signal(btc, news)
    return jsonify({"signal": signal})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
