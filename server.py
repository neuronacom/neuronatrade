import os, time, requests
from flask import Flask, jsonify
from flask_cors import CORS
import openai

# Ключи Heroku
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY")
BINANCE_SECRET = os.environ.get("BINANCE_SECRET")

# Публичные news API (GNews/Newsdata/Coingecko/Finage/cryptopanic)
NEWS_APIS = [
    "https://newsdata.io/api/1/news?apikey=pub_336810a07913f9a5e19f889ae982197d32492&q=bitcoin,crypto,blockchain&language=en",
    "https://gnews.io/api/v4/search?q=crypto&lang=en&token=91397e060e2ae8ee8e1dbd5d60725341"
]
CRYPTOPANIC_API = "https://cryptopanic.com/api/v1/posts/?auth_token=2cd2ebe38c9af9d7b50c0c0b9a5d0213e6798ccd&public=true"
COINGECKO_API = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,binancecoin&vs_currencies=usd"
CMC_API = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?limit=5"
CMC_KEY = "c3f5c286-e124-4f13-8da2-47fdb5f41051"

app = Flask(__name__)
CORS(app)

openai.api_key = OPENAI_API_KEY

@app.route("/api/news")
def api_news():
    out = []
    for url in NEWS_APIS:
        try:
            r = requests.get(url,timeout=8).json()
            arts = []
            if "results" in r: arts = r["results"]
            elif "articles" in r: arts = r["articles"]
            for n in arts:
                out.append({
                    "title": n.get("title") or n.get("title", ""),
                    "url": n.get("link") or n.get("url", ""),
                    "summary": n.get("description") or "",
                    "time": n.get("pubDate") or n.get("publishedAt") or "",
                    "source": n.get("source_id") or n.get("source", {}).get("name") or "",
                    "id": n.get("link") or n.get("url") or n.get("title"),
                    "impact": ""
                })
        except: pass
    # Добавляем cryptopanic
    try:
        r = requests.get(CRYPTOPANIC_API,timeout=6).json()
        for n in r.get("results",[]):
            out.append({
                "title": n["title"],
                "url": n["url"],
                "summary": n.get("description") or "",
                "time": n.get("published_at") or "",
                "source": "cryptopanic",
                "id": n["url"],
                "impact": n.get("currencies", [{}])[0].get("code") if n.get("currencies") else ""
            })
    except: pass
    # Сортировка новые сверху
    out.sort(key=lambda x:x["time"] or "", reverse=True)
    return jsonify({"articles": out[:20]})

@app.route("/api/comment")
def api_comment():
    # Комментарий от ИИ по рынку (BTC)
    try:
        prices = requests.get(COINGECKO_API).json()
        btc = prices.get("bitcoin",{}).get("usd","-")
        eth = prices.get("ethereum",{}).get("usd","-")
    except: btc,eth="-","-"
    try:
        news = requests.get(CRYPTOPANIC_API,timeout=5).json()
        last_news = news.get("results",[])[:2]
        last_headlines = " | ".join([n.get("title","") for n in last_news])
    except: last_headlines = ""
    prompt = (
        f"Дай свежий краткий торговый сигнал (LONG/SHORT/HODL) по BTC/USDT только по анализу графика, объёма и стакана Binance и новостей. "
        f"Только 1 сигнал с точкой входа и обоснованием! Укажи цену BTC (${btc}), цену ETH (${eth}), последняя новость: {last_headlines}.\n"
        f"В конце дай кратко твой прогноз до конца суток, поддержка/сопротивление. Только для трейдеров. Не используй слова ChatGPT/OpenAI. "
    )
    comment = ""
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role":"system","content":"Ты топ крипто-трейдер, делай анализ кратко, как для профи, максимум инфы!"},
                      {"role":"user","content":prompt}],
            temperature=1.18,max_tokens=480,timeout=17
        )
        comment = resp.choices[0].message.content.strip()
    except Exception as e:
        comment = f"Ошибка анализа рынка: {str(e)}"
    out = [{
        "text": comment,
        "time": time.strftime('%H:%M')
    }]
    return jsonify({"comments":out,"typing":False})

@app.route("/api/cmc")
def api_cmc():
    try:
        r = requests.get(CMC_API,headers={"X-CMC_PRO_API_KEY":CMC_KEY},timeout=7).json()
        return jsonify(r)
    except: return jsonify({"data":[]})

@app.route("/api/coingecko")
def api_coingecko():
    try:
        q = (requests.request.args.get("q") or "").lower()
        ids = {"btc":"bitcoin","eth":"ethereum","sol":"solana","bnb":"binancecoin"}
        id = ids.get(q.lower(),q.lower())
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={id}&vs_currencies=usd"
        r = requests.get(url,timeout=4).json()
        if id in r:
            return jsonify({"found":True,"name":id.title(),"symbol":q.upper(),"price":r[id]["usd"],"url":f"https://coingecko.com/en/coins/{id}"})
    except: pass
    return jsonify({"found":False})

@app.route("/api/binance")
def api_binance():
    try:
        symbol = (requests.request.args.get("q") or "BTC").upper()+"USDT"
        url = f"https://api.binance.com/api/v3/ticker/bookTicker?symbol={symbol}"
        r = requests.get(url,timeout=4).json()
        return jsonify({"found":True,"price":r.get("bidPrice") or r.get("askPrice"),"symbol":symbol})
    except: return jsonify({"found":False})

@app.route("/")
def index():
    return open("index.html").read()
