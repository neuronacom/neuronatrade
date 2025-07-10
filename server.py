import os
import requests
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
import openai

app = Flask(__name__, static_folder='static')
CORS(app)

BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY", "")
BINANCE_SECRET = os.environ.get("BINANCE_SECRET", "")
CRYPTOPANIC_API_KEY = os.environ.get("CRYPTOPANIC_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

def get_binance_btc_data():
    try:
        base_url = "https://api.binance.com"
        depth_resp = requests.get(f"{base_url}/api/v3/depth?symbol=BTCUSDT&limit=10")
        print("Binance DEPTH:", depth_resp.text, flush=True)
        depth = depth_resp.json()
        ticker_resp = requests.get(f"{base_url}/api/v3/ticker/24hr?symbol=BTCUSDT")
        print("Binance TICKER:", ticker_resp.text, flush=True)
        ticker = ticker_resp.json()
        return {
            "bids": depth.get("bids", []),
            "asks": depth.get("asks", []),
            "lastPrice": ticker.get("lastPrice"),
            "volume": ticker.get("volume"),
            "priceChangePercent": ticker.get("priceChangePercent")
        }
    except Exception as e:
        print("Binance API ERROR:", e, flush=True)
        return {"asks":[],"bids":[],"lastPrice":None,"priceChangePercent":None,"volume":None}

def get_cryptopanic_news():
    try:
        url = f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTOPANIC_API_KEY}&currencies=BTC&public=true"
        resp = requests.get(url)
        print("CryptoPanic RESP:", resp.text, flush=True)
        news = resp.json()
        result = []
        for n in news.get('results', [])[:10]:
            result.append({
                "title": n.get('title', ''),
                "url": n.get('url', n.get('source', {}).get('url', '#')),
                "published_at": n.get("published_at", '')
            })
        return result
    except Exception as e:
        print("CryptoPanic ERROR:", e, flush=True)
        return []

def ai_btc_signal(data, news):
    try:
        import openai
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        messages = [
            {"role": "system", "content": "Ты профессиональный трейдер криптовалют. Дай краткий анализ BTC/USDT на основе стакана, объёмов, новостей и индикаторов (RSI, MA, MACD, OBV, OrderBook). Твои сигналы: LONG, SHORT, HOLD. Пример ответа: 'Сигнал: LONG от 58900, SL 58000, TP 60000. Комментарий: ...'"},
            {"role": "user", "content": f"Данные Binance: {data}\nНовости: {news}"}
        ]
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=350
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("OPENAI ERROR:", e, flush=True)
        return "Ошибка AI: " + str(e)

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
    try:
        btc = get_binance_btc_data()
        news = get_cryptopanic_news()
        print("API_DATA OK", flush=True)
        return jsonify({"btc": btc, "news": news})
    except Exception as e:
        print("api_data ERROR:", e, flush=True)
        return jsonify({"btc": {}, "news": [], "error": str(e)}), 500

@app.route("/api/signal")
def api_signal():
    try:
        btc = get_binance_btc_data()
        news = get_cryptopanic_news()
        signal = ai_btc_signal(btc, news)
        print("API_SIGNAL OK", flush=True)
        return jsonify({"signal": signal})
    except Exception as e:
        print("api_signal ERROR:", e, flush=True)
        return jsonify({"signal": "Ошибка: "+str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
