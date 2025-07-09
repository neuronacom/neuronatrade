import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai

app = Flask(__name__)
CORS(app)

BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY", "")
CRYPTOPANIC_API_KEY = os.environ.get("CRYPTOPANIC_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

### --- CryptoPanic: Свежие важные новости --- ###
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
                "published_at": n.get("published_at", "")[:16].replace("T", " "),
                "source": n.get("source", {}).get("title", "cryptopanic")
            })
        return news
    except Exception:
        return []

### --- Binance: Цена и объём BTCUSDT --- ###
def get_btc_binance():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/24hr", params={"symbol": "BTCUSDT"})
        r.raise_for_status()
        data = r.json()
        return {
            "price": data["lastPrice"],
            "volume": data["volume"],
            "change": data["priceChangePercent"],
            "high": data["highPrice"],
            "low": data["lowPrice"],
            "quoteVolume": data["quoteVolume"],
            "timestamp": data.get("closeTime", 0)
        }
    except Exception:
        return {}

### --- Binance: Стакан BTCUSDT --- ###
def get_btc_orderbook():
    try:
        r = requests.get("https://api.binance.com/api/v3/depth", params={"symbol": "BTCUSDT", "limit": 10})
        r.raise_for_status()
        ob = r.json()
        return {
            "bids": ob.get("bids", []), # [[price, qty], ...]
            "asks": ob.get("asks", [])
        }
    except Exception:
        return {"bids": [], "asks": []}

### --- AI-анализ BTCUSDT (1 сигнал) --- ###
def analyze_btc_signal(price, orderbook, news):
    prompt = f"""
Анализируй BTC/USDT на Binance:
- Текущая цена: {price.get("price", "n/a")}
- 24h объем: {price.get("volume", "n/a")}
- 24h изменение: {price.get("change", "n/a")}
- 24h High/Low: {price.get("high", "n/a")} / {price.get("low", "n/a")}
- Стакан BID (10): {orderbook.get("bids", [])}
- Стакан ASK (10): {orderbook.get("asks", [])}
- Важные новости: {json.dumps(news, ensure_ascii=False)}

Дай кратко по TradingView-стилю:
BTC [LONG/SHORT] | Вход: [цена] TP: [цена] SL: [цена]
Комментарий: (1-2 предложения, четко по рынку! Только BTC!)
    """.strip()
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Ты профи-трейдер и даёшь только BTC сигналы и очень краткие комментарии, анализируешь стакан и объём."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.13,
            max_tokens=320
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Ошибка AI анализа: {str(e)}"

### --- API: Получить актуальный BTC сигнал --- ###
@app.route('/api/signal', methods=['GET'])
def api_signal():
    price = get_btc_binance()
    orderbook = get_btc_orderbook()
    news = get_cryptopanic_news(limit=2)
    signal = analyze_btc_signal(price, orderbook, news)
    return jsonify({
        "signal": signal,
        "price": price,
        "orderbook": orderbook,
        "news": news
    })

### --- API: Только Binance --- ###
@app.route('/api/binance', methods=['GET'])
def api_binance():
    return jsonify(get_btc_binance())

### --- API: Только стакан --- ###
@app.route('/api/orderbook', methods=['GET'])
def api_orderbook():
    return jsonify(get_btc_orderbook())

### --- API: Только новости --- ###
@app.route('/api/news', methods=['GET'])
def api_news():
    return jsonify(get_cryptopanic_news(limit=8))

### --- Healthcheck --- ###
@app.route('/')
def healthcheck():
    return 'CryptoAI server running!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
