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

# Получаем свежие важные новости с CryptoPanic
def get_cryptopanic_news(limit=2):
    url = f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTOPANIC_API_KEY}&filter=important"
    r = requests.get(url)
    news = []
    if r.ok:
        for n in r.json().get("results", [])[:limit]:
            dt = n.get("published_at", "")
            title = n.get("title", "")
            link = n.get("url", "")
            news.append({
                "title": title,
                "link": link,
                "datetime": dt
            })
    return news

# Цена и объём BTCUSDT с Binance
def get_btc_binance():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    params = {"symbol": "BTCUSDT"}
    r = requests.get(url, params=params)
    try:
        data = r.json()
        return {
            "price": data["lastPrice"],
            "volume": data["volume"],
            "change": data["priceChangePercent"],
            "high": data["highPrice"],
            "low": data["lowPrice"],
            "quoteVolume": data["quoteVolume"]
        }
    except Exception:
        return {}

# Стакан (orderbook) BTCUSDT с Binance (топ-10)
def get_btc_orderbook():
    url = "https://api.binance.com/api/v3/depth"
    params = {"symbol": "BTCUSDT", "limit": 10}
    r = requests.get(url, params=params)
    try:
        ob = r.json()
        return {
            "bids": ob["bids"], # [[price, qty], ...]
            "asks": ob["asks"]
        }
    except Exception:
        return {"bids": [], "asks": []}

# AI анализ BTC с реальными данными Binance (цена, объём, стакан) + свежие новости
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
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Ты опытный AI трейдер. Даёшь только точные сигналы и краткие комментарии, обязательно анализируешь стакан."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.15,
        max_tokens=350
    )
    return response.choices[0].message.content

@app.route('/api/stream', methods=['GET'])
def api_stream():
    news = get_cryptopanic_news(limit=1)
    price = get_btc_binance()
    orderbook = get_btc_orderbook()
    ai_signal = analyze_btc(price, orderbook, news)
    return jsonify({
        "news": news,
        "signal": ai_signal
    })

@app.route('/api/news', methods=['GET'])
def api_news():
    return jsonify(get_cryptopanic_news(limit=8))

@app.route('/')
def healthcheck():
    return 'CryptoAI server running!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
