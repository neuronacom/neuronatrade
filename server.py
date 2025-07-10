import os
import requests
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import openai
import datetime
import time

app = Flask(__name__, static_folder="static")
CORS(app)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")

openai.api_key = OPENAI_API_KEY

CACHE = {"signals": [], "news": [], "last_ts": 0}

def get_time(ts=None):
    dt = datetime.datetime.utcfromtimestamp(ts or time.time())
    return dt.strftime('%d.%m %H:%M')

def get_binance_orderbook():
    try:
        r = requests.get("https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=50", timeout=4)
        j = r.json()
        bids = float(j["bids"][0][0])
        asks = float(j["asks"][0][0])
        return {"bids": bids, "asks": asks}
    except Exception as ex:
        print("BINANCE ERROR:", ex)
        return {"bids": "-", "asks": "-"}

def get_coingecko_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=4)
        return r.json()["bitcoin"]["usd"]
    except Exception as ex:
        print("COINGECKO ERROR:", ex)
        return "-"

# NewsData API (регистрация нужна)
def get_newsdata_news():
    try:
        if not NEWS_API_KEY: return []
        url = f"https://newsdata.io/api/1/news?apikey={NEWS_API_KEY}&q=bitcoin,crypto,cryptocurrency&language=ru"
        r = requests.get(url, timeout=5)
        arr = []
        for a in r.json().get("results", [])[:5]:
            arr.append({
                "id": a.get("article_id", a.get("link", "")),
                "title": a["title"][:110],
                "url": a["link"],
                "time": a.get("pubDate", "")[-8:-3] if "pubDate" in a else ""
            })
        return arr
    except Exception as ex:
        print("NEWSDATA ERROR:", ex)
        return []

# CryptoPanic API (может без ключа, ограничено)
def get_cryptopanic_news():
    try:
        url = "https://cryptopanic.com/api/v1/posts/?auth_token=&public=true&currencies=BTC,ETH"
        r = requests.get(url, timeout=6)
        arr = []
        for a in r.json().get("results", [])[:5]:
            arr.append({
                "id": a.get("id"),
                "title": a["title"][:110],
                "url": a["url"],
                "time": a["published_at"][11:16] if "published_at" in a else ""
            })
        return arr
    except Exception as ex:
        print("CRYPTOPANIC ERROR:", ex)
        return []

# CoinDesk бесплатный (EN)
def get_coindesk_news():
    try:
        url = "https://api.coindesk.com/v1/news/latest"
        r = requests.get(url, timeout=5)
        arr = []
        for a in r.json().get("data", [])[:5]:
            arr.append({
                "id": a["id"],
                "title": a["headline"][:110],
                "url": a["url"],
                "time": a["published_at"][11:16] if "published_at" in a else ""
            })
        return arr
    except Exception as ex:
        print("COINDESK ERROR:", ex)
        return []

# CryptoCompare (EN, бесплатный, но только заголовки)
def get_cryptocompare_news():
    try:
        url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
        r = requests.get(url, timeout=5)
        arr = []
        for a in r.json().get("Data", [])[:5]:
            arr.append({
                "id": a["id"],
                "title": a["title"][:110],
                "url": a["url"],
                "time": a["published_on"] if "published_on" in a else ""
            })
        return arr
    except Exception as ex:
        print("CRYPTOCOMPARE ERROR:", ex)
        return []

def gen_ai_signal(price, ob, news):
    prompt = f"""Ты — криптоаналитик-бот NEURONA. Проанализируй Bitcoin (BTC/USDT) и дай максимально точный и обоснованный сигнал: LONG, SHORT или HODL, с коротким комментарием на русском. Данные: стакан Binance (bid: {ob['bids']} ask: {ob['asks']}), цена {price}$, свежие новости: {'; '.join([n['title'] for n in news[:3]])}. Отвечай только по-русски, кратко и строго по делу."""
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.22,
            max_tokens=150,
        )
        content = completion.choices[0].message["content"]
        signal_type = "HODL"
        if "LONG" in content.upper() or "ЛОНГ" in content.upper():
            signal_type = "LONG"
        elif "SHORT" in content.upper() or "ШОРТ" in content.upper():
            signal_type = "SHORT"
        return {
            "id": int(time.time()),
            "type": signal_type,
            "text": content,
            "time": get_time()
        }
    except Exception as e:
        print("OPENAI ERROR:", e)
        return {
            "id": int(time.time()),
            "type": "HODL",
            "text": "Анализ временно недоступен.",
            "time": get_time()
        }

@app.route("/")
def index():
    return send_from_directory('.', 'index.html')

@app.route("/manifest.json")
def manifest():
    return send_from_directory('.', 'manifest.json')

@app.route("/sw.js")
def sw():
    return send_from_directory('.', 'sw.js')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.route("/api/all")
def api_all():
    now = time.time()
    if now - CACHE["last_ts"] > 55:
        price = get_coingecko_price()
        ob = get_binance_orderbook()
        news = []
        # собираем все доступные новости (без дублирования id)
        news_sources = [
            get_newsdata_news(),
            get_coindesk_news(),
            get_cryptopanic_news(),
            get_cryptocompare_news(),
        ]
        ids = set()
        for src in news_sources:
            for n in src:
                if n['id'] not in ids:
                    news.append(n)
                    ids.add(n['id'])
        news = sorted(news, key=lambda x: str(x['time']))[-8:]
        ai_signal = gen_ai_signal(price, ob, news)
        CACHE["signals"].append(ai_signal)
        CACHE["signals"] = CACHE["signals"][-10:]
        CACHE["news"] = news[-8:]
        CACHE["last_ts"] = now
    return jsonify({
        "signals": CACHE["signals"][-10:],
        "news": CACHE["news"][-3:]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
