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
COINMARKETCAP_API_KEY = os.environ.get("COINMARKETCAP_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Get fresh CryptoPanic news
def get_cryptopanic_news(limit=3):
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

# Latest prices
def get_coinmarketcap_prices():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    params = {"symbol": "BTC,ETH,BNB,SOL,XRP"}
    headers = {"X-CMC_PRO_API_KEY": COINMARKETCAP_API_KEY}
    r = requests.get(url, headers=headers, params=params)
    return r.json()

# Orderbook snapshot (top 10 bids/asks)
def get_binance_order_book(symbol="BTCUSDT", limit=10):
    url = f"https://api.binance.com/api/v3/depth"
    params = {"symbol": symbol, "limit": limit}
    r = requests.get(url, params=params)
    return r.json() if r.ok else {}

# Compose AI prompt with **orderbook and volumes**
def analyze_market_and_generate_signals(prices, order_books, news, timeframe):
    prompt = f"""Тебе даны:
- Свежие цены CoinMarketCap: {json.dumps(prices)}
- Binance стаканы (топ 10 заявок по каждому активу): {json.dumps(order_books)}
- Последние 3 важные новости: {json.dumps(news, ensure_ascii=False)}
    
Детально проанализируй объёмы в стаканах (ищи дисбаланс, плотности, спуфинг), дай прогноз движения и СИГНАЛЫ на {timeframe} по BTC, ETH, BNB, SOL, XRP.

Для каждой монеты: 
- Укажи направление (LONG/SHORT), цену входа, TP, SL
- По стаканам выдели явные точки входа, если видно
- Кратко прокомментируй ситуацию по рынку

Сообщения пиши компактно и понятно.

Формат:
[coin] [LONG/SHORT] | Вход: [price] TP: [price] SL: [price]
Комментарий: ..."""

    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Ты профессиональный AI-криптотрейдер, очень кратко и понятно освещаешь рынок и даёшь сигналы, не повторяй новости."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.25,
        max_tokens=800
    )
    return response.choices[0].message.content

# ---- API ----

@app.route('/api/stream', methods=['GET'])
def api_stream():
    # Отдаем последние 1-2 новости и один свежий сигнал (чередуем)
    timeframe = request.args.get("tf", "15m")
    news = get_cryptopanic_news(limit=1)
    prices = get_coinmarketcap_prices()
    order_books = {p: get_binance_order_book(p) for p in ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT"]}
    ai_signal = analyze_market_and_generate_signals(prices, order_books, news, timeframe)
    return jsonify({
        "news": news,
        "signal": ai_signal
    })

@app.route('/api/news', methods=['GET'])
def api_news():
    return jsonify(get_cryptopanic_news(limit=10))

@app.route('/')
def healthcheck():
    return 'CryptoAI server running!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
