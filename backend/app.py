import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import openai

app = Flask(__name__)
CORS(app)

# Все ключи теперь только из переменных окружения!
BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY", "")
CRYPTOPANIC_API_KEY = os.environ.get("CRYPTOPANIC_API_KEY", "")
COINMARKETCAP_API_KEY = os.environ.get("COINMARKETCAP_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

openai.api_key = OPENAI_API_KEY

def get_cryptopanic_news():
    url = f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTOPANIC_API_KEY}&filter=important"
    r = requests.get(url)
    news = []
    if r.ok:
        for n in r.json().get("results", []):
            dt = n.get("published_at", "")
            title = n.get("title", "")
            link = n.get("url", "")
            news.append({
                "title": title,
                "link": link,
                "datetime": dt
            })
    return news

def get_coinmarketcap_prices():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    params = {"symbol": "BTC,ETH,BNB,SOL,XRP"}
    headers = {"X-CMC_PRO_API_KEY": COINMARKETCAP_API_KEY}
    r = requests.get(url, headers=headers, params=params)
    return r.json()

def get_binance_order_book(symbol="BTCUSDT", limit=50):
    url = f"https://api.binance.com/api/v3/depth"
    params = {"symbol": symbol, "limit": limit}
    r = requests.get(url, params=params)
    return r.json()

def analyze_market_and_generate_signals(prices, order_books, news, timeframe):
    prompt = f"""
    Тебе даются свежие цены с CoinMarketCap: {json.dumps(prices)}.
    Актуальные стаканы Binance: {json.dumps(order_books)}.
    Последние важные новости: {json.dumps(news[:3], ensure_ascii=False)}.
    Дай свой AI-комментарий, укажи общий тренд, и ДАЙ СИГНАЛЫ (LONG/SHORT + где вход и выход) для BTC, ETH, BNB, SOL, XRP на {timeframe} графике.
    Сигналы должны быть в формате:
    [COIN] [LONG/SHORT] | Вход: [уровень], TP: [уровень], SL: [уровень]
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Ты опытный AI-трейдер, эксперт по фьючерсам, всегда четко и кратко даешь рекомендации и рыночные обзоры на русском."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
        max_tokens=900
    )
    return response.choices[0].message['content']

@app.route('/api/news', methods=['GET'])
def api_news():
    news = get_cryptopanic_news()
    return jsonify(news)

@app.route('/api/prices', methods=['GET'])
def api_prices():
    prices = get_coinmarketcap_prices()
    return jsonify(prices)

@app.route('/api/orderbook', methods=['GET'])
def api_orderbook():
    pairs = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]
    order_books = {}
    for pair in pairs:
        order_books[pair] = get_binance_order_book(pair)
    return jsonify(order_books)

@app.route('/api/analyze', methods=['GET'])
def api_analyze():
    timeframe = request.args.get("tf", "15m")
    prices = get_coinmarketcap_prices()
    order_books = {}
    for pair in ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]:
        order_books[pair] = get_binance_order_book(pair)
    news = get_cryptopanic_news()
    result = analyze_market_and_generate_signals(prices, order_books, news, timeframe)
    return jsonify({"ai": result})

@app.route('/')
def healthcheck():
    return 'CryptoAI server running!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
