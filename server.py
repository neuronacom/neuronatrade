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

CACHE = {
    "signals": [],
    "news": [],
    "last_ts": 0,
    "last_price": None,
    "last_news_id": None,
    "last_orderbook": None,
}

def get_time(ts=None):
    dt = datetime.datetime.fromtimestamp(ts or time.time())
    return dt.strftime('%d.%m %H:%M')

def get_binance_orderbook():
    try:
        r = requests.get("https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=5", timeout=3)
        j = r.json()
        bids = float(j["bids"][0][0])
        asks = float(j["asks"][0][0])
        return {"bids": bids, "asks": asks}
    except Exception as ex:
        print("BINANCE ERROR:", ex)
        return {"bids": "-", "asks": "-"}

def get_coingecko_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=3)
        return r.json()["bitcoin"]["usd"]
    except Exception as ex:
        print("COINGECKO ERROR:", ex)
        return "-"

def get_newsdata_news():
    try:
        if not NEWS_API_KEY:
            return []
        url = f"https://newsdata.io/api/1/news?apikey={NEWS_API_KEY}&q=bitcoin,crypto,cryptocurrency&language=en"
        r = requests.get(url, timeout=6)
        arr = []
        for a in r.json().get("results", [])[:6]:
            arr.append({
                "id": a.get("article_id", a.get("link", "")),
                "title": a["title"][:110],
                "url": a["link"],
                "time": a.get("pubDate", "")[11:16] if "pubDate" in a else "",
                "src": "newsdata"
            })
        return arr
    except Exception as ex:
        print("NEWSDATA ERROR:", ex)
        return []

def get_cryptopanic_news():
    try:
        url = "https://cryptopanic.com/api/v1/posts/?auth_token=&public=true&currencies=BTC,ETH"
        r = requests.get(url, timeout=6)
        arr = []
        for a in r.json().get("results", [])[:6]:
            arr.append({
                "id": a.get("id"),
                "title": a["title"][:110],
                "url": a["url"],
                "time": a["published_at"][11:16] if "published_at" in a else "",
                "src": "cryptopanic"
            })
        return arr
    except Exception as ex:
        print("CRYPTOPANIC ERROR:", ex)
        return []

def get_coindesk_news():
    try:
        url = "https://api.coindesk.com/v1/news/latest"
        r = requests.get(url, timeout=6)
        arr = []
        for a in r.json().get("data", [])[:6]:
            arr.append({
                "id": a["id"],
                "title": a["headline"][:110],
                "url": a["url"],
                "time": a["published_at"][11:16] if "published_at" in a else "",
                "src": "coindesk"
            })
        return arr
    except Exception as ex:
        print("COINDESK ERROR:", ex)
        return []

def get_cryptocompare_news():
    try:
        url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
        r = requests.get(url, timeout=6)
        arr = []
        for a in r.json().get("Data", [])[:6]:
            arr.append({
                "id": a["id"],
                "title": a["title"][:110],
                "url": a["url"],
                "time": datetime.datetime.fromtimestamp(a.get("published_on", 0)).strftime("%H:%M"),
                "src": "cryptocompare"
            })
        return arr
    except Exception as ex:
        print("CRYPTOCOMPARE ERROR:", ex)
        return []

def translate_text(text):
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": f"Переведи на русский кратко и понятно:\n\n{text}"}
            ],
            temperature=0.15,
            max_tokens=130,
        )
        return completion.choices[0].message["content"]
    except Exception as ex:
        print("TRANSLATE ERROR:", ex)
        return text

def gen_ai_signal(price, ob, news):
    news_titles = [n['title'] for n in news[:3]]
    prompt = f"""Ты — криптоаналитик-бот NEURONA. Проанализируй Bitcoin (BTC/USDT) и дай максимально точный и обоснованный сигнал: LONG, SHORT или HODL, с коротким комментарием на русском. Данные: стакан Binance (bid: {ob['bids']} ask: {ob['asks']}), цена {price}$, свежие новости: {'; '.join(news_titles)}. Отвечай только по-русски, кратко и строго по делу."""
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.18,
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
    price = get_coingecko_price()
    ob = get_binance_orderbook()
    news_sources = [
        get_newsdata_news(),
        get_coindesk_news(),
        get_cryptopanic_news(),
        get_cryptocompare_news(),
    ]
    news = []
    ids = set()
    for src in news_sources:
        for n in src:
            if n['id'] not in ids:
                # Переводим новость
                n['title'] = translate_text(n['title'])
                news.append(n)
                ids.add(n['id'])
    news = sorted(news, key=lambda x: str(x['time']))[-8:]

    # Если изменилась цена, новости или стакан — только тогда делаем новый анализ
    do_analyze = False
    if (
        CACHE['last_price'] != price
        or CACHE['last_news_id'] != (news[-1]['id'] if news else None)
        or CACHE['last_orderbook'] != ob
    ):
        do_analyze = True

    if do_analyze:
        ai_signal = gen_ai_signal(price, ob, news)
        CACHE["signals"].append(ai_signal)
        CACHE["signals"] = CACHE["signals"][-10:]
        CACHE['last_price'] = price
        CACHE['last_news_id'] = news[-1]['id'] if news else None
        CACHE['last_orderbook'] = ob
        CACHE["news"] = news[-8:]
        CACHE["last_ts"] = now

    return jsonify({
        "signals": CACHE["signals"][-10:],
        "news": CACHE["news"][-3:]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
