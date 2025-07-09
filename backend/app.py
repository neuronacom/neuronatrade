import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai

app = Flask(__name__)
CORS(app)

CRYPTOPANIC_API_KEY = os.environ.get("CRYPTOPANIC_API_KEY", "")
COINMARKETCAP_API_KEY = os.environ.get("COINMARKETCAP_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Новости (1-2 свежих)
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

# Цена BTC с CoinMarketCap
def get_btc_price():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    params = {"symbol": "BTC"}
    headers = {"X-CMC_PRO_API_KEY": COINMARKETCAP_API_KEY}
    r = requests.get(url, headers=headers, params=params)
    try:
        return r.json()["data"]["BTC"]
    except Exception:
        return {}

# AI анализ только BTC + TradingView
def analyze_btc_tradingview(price, news):
    prompt = f"""
    Вот свежие данные по биткоину:
    - Цена: {price.get('quote', {}).get('USD', {}).get('price', 'n/a')}
    - Изменения за 1ч: {price.get('quote', {}).get('USD', {}).get('percent_change_1h', 'n/a')}
    - Изменения за 24ч: {price.get('quote', {}).get('USD', {}).get('percent_change_24h', 'n/a')}
    - Изменения за 7д: {price.get('quote', {}).get('USD', {}).get('percent_change_7d', 'n/a')}
    - Капитализация: {price.get('quote', {}).get('USD', {}).get('market_cap', 'n/a')}
    - Объём 24ч: {price.get('quote', {}).get('USD', {}).get('volume_24h', 'n/a')}
    Последние новости: {json.dumps(news, ensure_ascii=False)}
    
    Проведи анализ ситуации по BTC на основе этих данных, а также максимального набора индикаторов TradingView (RSI, MACD, EMA, объёмы, Price Action). 
    Выдай **ТОЧНЫЙ ТРЕЙДИНГ СИГНАЛ (LONG/SHORT)** на ближайшие 15 минут с указанием:
    - Вход (примерное значение)
    - TP
    - SL
    - Таймфрейм: 15m
    - Очень краткий комментарий (1-2 предложения), опираясь на новости, динамику, индикаторы (без воды!)
    Сигнал выдай в формате:
    BTC [LONG/SHORT] | Вход: [price] TP: [price] SL: [price]
    Комментарий: ..."""

    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Ты очень опытный AI-криптотрейдер. Отвечай предельно лаконично и по сути. Используй реальные данные и технический анализ."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.18,
        max_tokens=400
    )
    return response.choices[0].message.content

@app.route('/api/stream', methods=['GET'])
def api_stream():
    news = get_cryptopanic_news(limit=1)
    price = get_btc_price()
    ai_signal = analyze_btc_tradingview(price, news)
    return jsonify({
        "news": news,
        "signal": ai_signal
    })

@app.route('/')
def healthcheck():
    return 'CryptoAI server running!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
