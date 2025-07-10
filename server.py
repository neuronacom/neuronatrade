import os
import requests
from flask import Flask, jsonify
from flask_cors import CORS
from openai import OpenAI
import datetime

app = Flask(__name__)
CORS(app)

BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY", "")
BINANCE_SECRET = os.environ.get("BINANCE_SECRET", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Публичные источники новостей
CRYPTO_NEWS_APIS = [
    ("CryptoPanic", "https://cryptopanic.com/api/v1/posts/?auth_token=2cd2ebe38c9af9d7b50c0c0b9a5d0213e6798ccd&currencies=BTC&public=true"),
    ("GNews", "https://gnews.io/api/v4/search?q=bitcoin&lang=ru&token=6b682e3e057eb47e9b3a330d3871a234"),
    ("CoinGecko", "https://api.coingecko.com/api/v3/status_updates?category=general"),
]

def get_crypto_news():
    news = []
    for source, url in CRYPTO_NEWS_APIS:
        try:
            resp = requests.get(url, timeout=4)
            if resp.ok:
                data = resp.json()
                if "results" in data:  # CryptoPanic
                    for x in data["results"][:6]:
                        news.append({
                            "title": x["title"],
                            "link": x["url"],
                            "time": x.get("published_at", "")[:16].replace("T", " ").replace("Z","")
                        })
                elif "articles" in data:  # GNews
                    for x in data["articles"][:6]:
                        news.append({
                            "title": x["title"],
                            "link": x["url"],
                            "time": x.get("publishedAt", "")[:16].replace("T", " ").replace("Z","")
                        })
                elif "status_updates" in data:  # CoinGecko
                    for x in data["status_updates"][:4]:
                        news.append({
                            "title": x["description"][:80]+"...",
                            "link": x["project"]["homepage"] if x["project"] else "https://coingecko.com",
                            "time": x["created_at"][:16].replace("T", " ").replace("Z","")
                        })
                if len(news) > 8: break
        except Exception: continue
    return news[:8]

def get_binance_data():
    url = "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"
    try:
        r = requests.get(url, timeout=3)
        d = r.json()
        return {
            "price": d.get("lastPrice", "-"),
            "vol24": round(float(d.get("volume", 0)), 3),
            "chg24": round(float(d.get("priceChangePercent", 0)), 2)
        }
    except Exception:
        return {"price": "-", "vol24": "-", "chg24": "-"}

def get_ai_signal(price, vol, chg):
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        messages = [
            {"role":"system","content":"Ты — лучший в мире трейдинг-бот по BTC. Дай подробный анализ ситуации по BTC/USDT с точкой входа, текущим трендом, рекомендацией LONG, SHORT или HODL, обязательно укажи причину. Если сигнал — распиши логически. Используй анализ графика, стаканов, индикаторов, последних новостей."},
            {"role":"user","content":f"Цена: {price}$, Объём 24ч: {vol}, Изменение 24ч: {chg}%"}
        ]
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.13, max_tokens=350
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"AI: Ошибка AI: {e}"

@app.route('/api/news')
def api_news():
    news = get_crypto_news()
    return jsonify({"news": news})

@app.route('/api/signal')
def api_signal():
    data = get_binance_data()
    ai_text = get_ai_signal(data['price'], data['vol24'], data['chg24'])
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    signal = f"<b>Цена: {data['price']}$ — Объём 24ч: {data['vol24']}$ — Изм. 24ч: {data['chg24']}%</b><br>{ai_text}<br><b>Тренд:</b> -<br><b>Время:</b> {now}"
    return jsonify({"signal": signal})

@app.route('/')
def index():
    with open('index.html', encoding="utf-8") as f:
        return f.read()

@app.route('/main.css')
def main_css():
    with open('main.css', encoding="utf-8") as f:
        return f.read(), 200, {"Content-Type": "text/css"}

@app.route('/main.js')
def main_js():
    with open('main.js', encoding="utf-8") as f:
        return f.read(), 200, {"Content-Type": "application/javascript"}

@app.route('/manifest.json')
def manifest():
    with open('manifest.json', encoding="utf-8") as f:
        return f.read(), 200, {"Content-Type": "application/manifest+json"}

@app.route('/sw.js')
def sw():
    with open('sw.js', encoding="utf-8") as f:
        return f.read(), 200, {"Content-Type": "application/javascript"}

if __name__ == "__main__":
    app.run(debug=True)
