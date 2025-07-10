import os
import requests
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import openai

app = Flask(__name__, static_url_path='', static_folder='.')
CORS(app)

# API KEYS from Heroku env
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET = os.getenv("BINANCE_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Получение данных с Binance API
def get_binance_data():
    try:
        # Цена BTC
        price_r = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT').json()
        price = float(price_r['price'])
        # 24h stats
        stats = requests.get('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT').json()
        change = float(stats['priceChangePercent'])
        vol = float(stats['volume'])
        # Стакан
        book = requests.get('https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=10').json()
        best_ask = book['asks'][0][0]
        best_bid = book['bids'][0][0]
        return price, change, vol, best_ask, best_bid
    except Exception as e:
        return '-', '-', '-', '-', '-'

# --- Генерация AI-комментария
def ai_comment(price, change, vol, ask, bid):
    try:
        openai.api_key = OPENAI_API_KEY
        prompt = f"""
Ты — трейдинг-бот и эксперт по криптовалюте. Дай детальный, лаконичный анализ ситуации по BTC/USDT.
Цена: ${price}
Изменение 24ч: {change}%
Объем 24ч: {vol} BTC
Верх стакана: {ask}
Низ стакана: {bid}
Дай прогноз: LONG, SHORT или HODL? Опиши кратко обоснование с учетом тренда, объемов, стаканов, технических индикаторов (MA, RSI, OBV, Volume, уровни), новостного фона. Сформулируй четкий сигнал!
"""
        resp = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role":"user", "content": prompt}],
            max_tokens=180, temperature=0.35
        )
        msg = resp['choices'][0]['message']['content'].strip()
        direction = "LONG" if "LONG" in msg.upper() else ("SHORT" if "SHORT" in msg.upper() else "HODL")
        return direction, msg
    except Exception as e:
        return "-", "Ошибка AI: " + str(e)

@app.route('/api/signal')
def api_signal():
    price, change, vol, ask, bid = get_binance_data()
    direction, comment = ai_comment(price, change, vol, ask, bid)
    import datetime
    signal = {
        "price": price, "change": change, "volume": vol,
        "direction": direction, "comment": comment,
        "time": datetime.datetime.utcnow().isoformat()
    }
    return jsonify({"signal": signal})

@app.route('/api/news')
def api_news():
    news = []
    try:
        # News source 1: CoinStats (русские иногда бывают)
        r = requests.get('https://api.coinstats.app/public/v1/news?skip=0&limit=10&category=bitcoin').json()
        for n in r.get('news', []):
            news.append({
                "title": n['title'],
                "url": n['link'],
                "source": n['source'],
                "time": n['date'][-8:-3]
            })
        # News source 2: GNews (ru)
        r2 = requests.get('https://gnews.io/api/v4/search?q=bitcoin&lang=ru&token=4e5797c401fdb836b7e0ba726808adfd').json()
        for n in r2.get('articles', []):
            news.append({
                "title": n['title'],
                "url": n['url'],
                "source": n['source']['name'],
                "time": n['publishedAt'][11:16]
            })
        # Ограничить 8 новостей
        return jsonify({"news": news[:8]})
    except Exception as e:
        return jsonify({"news": [{"title": "Нет новостей", "url": "#", "source": "", "time": ""}]})

@app.route('/manifest.json')
def manifest(): return send_from_directory('.', 'manifest.json')
@app.route('/sw.js')
def sw(): return send_from_directory('.', 'sw.js')
@app.route('/')
def root(): return send_from_directory('.', 'index.html')
@app.route('/<path:path>')
def static_files(path): return send_from_directory('.', path)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
