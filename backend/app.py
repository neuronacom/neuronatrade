import os
import json
import requests
from flask import Flask, jsonify
from flask_cors import CORS
import openai

app = Flask(__name__)
CORS(app)

BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY", "")
CRYPTOPANIC_API_KEY = os.environ.get("CRYPTOPANIC_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

### --- CryptoPanic: Cвежие важные новости --- ###
def get_cryptopanic_news(limit=5):
    url = f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTOPANIC_API_KEY}&filter=important"
    try:
        r = requests.get(url)
        r.raise_for_status()
        results = r.json().get("results", [])
        news = []
        for n in results[:limit]:
            news.append({
                "title": n.get("title", ""),
                "url": n.get("url", ""),
                "published_at": n.get("published_at", ""),
                "source": n.get("source", {}).get("title", "cryptopanic")
            })
        return news
    except Exception as e:
        print("get_cryptopanic_news error:", e)
        return []

### --- Binance: Цена и объём BTCUSDT --- ###
def get_btc_binance():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/24hr", params={"symbol": "BTCUSDT"})
        data = r.json()
        return {
            "price": data.get("lastPrice", ""),
            "volume": data.get("volume", ""),
            "change": data.get("priceChangePercent", ""),
            "high": data.get("highPrice", ""),
            "low": data.get("lowPrice", ""),
            "quoteVolume": data.get("quoteVolume", "")
        }
    except Exception as e:
        print("get_btc_binance error:", e)
        return {}

### --- Binance: Orderbook BTCUSDT (топ-10) --- ###
def get_btc_orderbook():
    try:
        r = requests.get("https://api.binance.com/api/v3/depth", params={"symbol": "BTCUSDT", "limit": 10})
        ob = r.json()
        return {
            "bids": ob.get("bids", []), # [[price, qty], ...]
            "asks": ob.get("asks", [])
        }
    except Exception as e:
        print("get_btc_orderbook error:", e)
        return {"bids": [], "asks": []}

### --- AI-анализ BTC --- ###
def analyze_btc(price, orderbook, news):
    prompt = f"""
Текущая цена BTC/USDT на Binance: {price.get("price", "n/a")}
24h объём: {price.get("volume", "n/a")}
24h изменение: {price.get("change", "n/a")}
24h high/low: {price.get("high", "n/a")} / {price.get("low", "n/a")}
Топ-10 BID стакана: {orderbook.get("bids", [])}
Топ-10 ASK стакана: {orderbook.get("asks", [])}
Свежие важные новости: {json.dumps(news, ensure_ascii=False)}

Дай короткий, профессиональный трейдинг-анализ (TradingView style): учти цену, объём, дисбаланс стаканов, крупные лимитки, движения объёма и новостной фон.
Выдай только по BTC, 15-минутный сигнал:
BTC [LONG/SHORT] | Вход: [price] TP: [price] SL: [price]
Комментарий: (1-2 предложения, реально про цену и рынок, не воду!)
"""
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Ты опытный AI трейдер. Даёшь только точные сигналы и краткие комментарии, обязательно анализируешь стакан."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.11,
            max_tokens=330
        )
        return response.choices[0].message.content
    except Exception as e:
        print("analyze_btc error:", e)
        return "AI недоступен или ошибка анализа."

# --- API endpoints --- #

@app.route('/api/stream', methods=['GET'])
def api_stream():
    price = get_btc_binance()
    orderbook = get_btc_orderbook()
    news = get_cryptopanic_news(limit=3)
    ai_signal = analyze_btc(price, orderbook, news)
    return jsonify({
        "price": price,
        "orderbook": orderbook,
        "news": news,
        "signal": ai_signal
    })

@app.route('/api/news', methods=['GET'])
def api_news():
    news = get_cryptopanic_news(limit=8)
    return jsonify(news)

@app.route('/api/binance', methods=['GET'])
def api_binance():
    return jsonify(get_btc_binance())

@app.route('/api/orderbook', methods=['GET'])
def api_orderbook():
    return jsonify(get_btc_orderbook())

@app.route('/')
def healthcheck():
    return 'CryptoAI server running!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
