import os, requests, ccxt, time
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import openai

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY", "")
BINANCE_SECRET = os.environ.get("BINANCE_SECRET", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

NEWS_APIS = [
    'https://cryptopanic.com/api/v1/posts/?auth_token=2cd2ebe38c9af9d7b50c0c0b9a5d0213e6798ccd&public=true',
    'https://api.coinstats.app/public/v1/news?skip=0&limit=5',
    'https://cryptocontrol.io/api/v1/public/news/coin/bitcoin',
    'https://gnews.io/api/v4/search?q=bitcoin&token=5dd2c6e66e490b0e1195c795b63ef822',
]

def translate_ru(txt):
    try:
        url = "https://translate.astian.org/translate"
        resp = requests.post(url, json={"q": txt, "source": "en", "target": "ru", "format": "text"}, timeout=5)
        if resp.ok:
            return resp.json()["translatedText"]
    except: pass
    return txt

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory('.', path)

@app.route('/api/news')
def api_news():
    news = []
    for url in NEWS_APIS:
        try:
            r = requests.get(url, timeout=5)
            j = r.json()
            if "results" in j:
                articles = j["results"]
            elif "data" in j:
                articles = j["data"]
            elif "articles" in j:
                articles = j["articles"]
            elif "posts" in j:
                articles = j["posts"]
            else:
                articles = j if isinstance(j, list) else []
            for a in articles[:4]:
                title = a.get("title") or a.get("headline")
                if title and not any(x in title for x in ['Ethereum', 'Solana', 'XRP', 'Dogecoin']):
                    if a.get("lang") != "ru":
                        title = translate_ru(title)
                    news.append({
                        "id": a.get("id", None),
                        "title": title,
                        "url": a.get("url"),
                        "time": a.get("published_at") or a.get("published") or a.get("created_at"),
                        "source": url.split('/')[2]
                    })
        except Exception as ex:
            continue
    news = sorted(news, key=lambda x: x.get("time", ""), reverse=True)
    return jsonify({"articles": news[:12]})

@app.route('/api/signal')
def api_signal():
    # Получаем аналитику с Binance через ccxt
    try:
        exchange = ccxt.binance()
        orderbook = exchange.fetch_order_book('BTC/USDT')
        ticker = exchange.fetch_ticker('BTC/USDT')
        volume = round(ticker['quoteVolume'] / ticker['last'], 2)
        change = round(ticker['percentage'], 2)
        price = round(ticker['last'], 2)
        ob_top = orderbook['asks'][0][0] if orderbook['asks'] else '-'
        ob_bottom = orderbook['bids'][0][0] if orderbook['bids'] else '-'
        now = time.strftime("%Y-%m-%d %H:%M", time.gmtime())
    except Exception as ex:
        return jsonify({"signal": {
            "symbol": "BTC/USDT", "direction": "-", "price": "-", "volume": "-", "change": "-",
            "orderbook_top": "-", "orderbook_bottom": "-", "comment": "Ошибка Binance API: " + str(ex), "time": "-"
        }})
    # AI анализ сигнала
    direction = "LONG" if change > 0 else "SHORT"
    openai.api_key = OPENAI_API_KEY
    try:
        prompt = (
            f"Анализируй рынок BTC/USDT:\n"
            f"Цена: ${price}, 24ч объём: {volume} BTC, Изменение 24ч: {change}%, "
            f"Верх стакана: {ob_top}, Низ стакана: {ob_bottom}, Тренд: {'восходящий' if change > 0 else 'нисходящий'}.\n"
            f"Дай совет трейдеру (отвечай лаконично):"
        )
        ai_comment = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role":"system","content":"Ты крипто-аналитик."},{"role":"user","content":prompt}],
            max_tokens=70,
            temperature=0.22,
        ).choices[0].message.content
    except Exception as ex:
        ai_comment = "AI временно недоступен: "+str(ex)
    signal = {
        "symbol": "BTC/USDT",
        "direction": direction,
        "price": price,
        "volume": volume,
        "change": change,
        "orderbook_top": ob_top,
        "orderbook_bottom": ob_bottom,
        "comment": ai_comment,
        "time": now
    }
    return jsonify({"signal": signal})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
