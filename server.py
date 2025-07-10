import os
import requests
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import openai
import datetime
import time

app = Flask(__name__)
CORS(app)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY", "")
NEWS_API_KEYS = {
    "cryptopanic": "2cd2ebe38c9af9d7b50c0c0b9a5d0213e6798ccd",
    "newsdata": "pub_86551015ead451be862a2f2a758505e5355c4"
}
COIN_ID = "bitcoin"
SYMBOL = "BTCUSDT"

openai.api_key = OPENAI_API_KEY

CACHE = {"signals": [], "news": [], "last_ts": 0}

def get_time(ts=None):
    dt = datetime.datetime.utcfromtimestamp(ts or time.time())
    return dt.strftime('%d.%m %H:%M')

def get_binance_orderbook():
    try:
        r = requests.get("https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=50", timeout=3)
        j = r.json()
        bids = float(j["bids"][0][0])
        asks = float(j["asks"][0][0])
        return {"bids": bids, "asks": asks}
    except:
        return {"bids": "-", "asks": "-"}

def get_coingecko_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=3)
        return r.json()["bitcoin"]["usd"]
    except:
        return "-"

def get_cryptopanic_news():
    try:
        url = f"https://cryptopanic.com/api/v1/posts/?auth_token={NEWS_API_KEYS['cryptopanic']}&public=true"
        r = requests.get(url, timeout=5)
        arr = []
        for post in r.json().get("results", [])[:7]:
            arr.append({
                "id": post["id"],
                "title": post["title"],
                "url": post["url"],
                "time": datetime.datetime.fromisoformat(post["published_at"]).strftime('%H:%M')
            })
        return arr
    except Exception as ex:
        return []

def get_newsdata_news():
    try:
        url = f"https://newsdata.io/api/1/news?apikey={NEWS_API_KEYS['newsdata']}&q=bitcoin,crypto,cryptocurrency&language=ru"
        r = requests.get(url, timeout=5)
        arr = []
        for a in r.json().get("results", [])[:7]:
            arr.append({
                "id": a.get("article_id", a["link"]),
                "title": a["title"][:110],
                "url": a["link"],
                "time": a.get("pubDate", "")[-8:-3] if "pubDate" in a else ""
            })
        return arr
    except Exception as ex:
        return []

def gen_ai_signal(price,ob,news):
    prompt = f"""Ты — криптоаналитик-бот NEURONA, твоя задача — дать пользователю максимально точный и обоснованный сигнал по Bitcoin (BTC/USDT): LONG, SHORT или HODL, с кратким комментарием. Используй анализ стаканов Binance (bid: {ob['bids']} ask: {ob['asks']}), цену {price}$, последние новости: {'; '.join([n['title'] for n in news[:3]])}. Только факты и сильная аргументация на сегодня."""
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role":"user","content":prompt}],
            temperature=0.3,
            max_tokens=180,
        )
        content = completion.choices[0].message["content"]
        signal_type = "HODL"
        if "LONG" in content.upper():
            signal_type = "LONG"
        elif "SHORT" in content.upper():
            signal_type = "SHORT"
        return {
            "id": int(time.time()),
            "type": signal_type,
            "text": content,
            "time": get_time()
        }
    except Exception as e:
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

@app.route("/api/all")
def api_all():
    now = time.time()
    if now - CACHE["last_ts"] > 55:
        price = get_coingecko_price()
        ob = get_binance_orderbook()
        news_1 = get_cryptopanic_news()
        news_2 = get_newsdata_news()
        all_news = sorted(news_1+news_2, key=lambda x:x['time'])[-8:]
        ai_signal = gen_ai_signal(price,ob,all_news)
        CACHE["signals"].append(ai_signal)
        CACHE["signals"] = CACHE["signals"][-10:]
        CACHE["news"] = all_news[-8:]
        CACHE["last_ts"] = now
    return jsonify({
        "signals": CACHE["signals"][-10:],
        "news": CACHE["news"][-8:]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT", 5000)))
