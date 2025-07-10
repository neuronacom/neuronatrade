import os
import requests
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import openai

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Ключи — Heroku через env (OpenAI, Binance), публичные — здесь
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY", "")
BINANCE_SECRET = os.environ.get("BINANCE_SECRET", "")

# Публичные API для крипто-новостей (встроенные)
NEWS_APIS = [
    # CryptoPanic (public API, demo)
    'https://cryptopanic.com/api/v1/posts/?auth_token=2cd2ebe38c9af9d7b50c0c0b9a5d0213e6798ccd&public=true',
    # CryptoControl
    'https://cryptocontrol.io/api/v1/public/news/coin/bitcoin',
    # CoinStats News
    'https://api.coinstats.app/public/v1/news?skip=0&limit=5',
    # GNews
    'https://gnews.io/api/v4/search?q=bitcoin&token=5dd2c6e66e490b0e1195c795b63ef822',
]

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
            # Пытаемся вытянуть новости из разных структур
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
            # Форматируем
            for a in articles[:5]:
                news.append({
                    "title": a.get("title") or a.get("headline"),
                    "url": a.get("url"),
                    "time": a.get("published_at") or a.get("published") or a.get("created_at"),
                    "source": url.split('/')[2]
                })
        except Exception as ex:
            continue
    # Сортировка по времени (самые свежие)
    news = sorted(news, key=lambda x: x.get("time", ""), reverse=True)
    return jsonify({"articles": news[:8]})

@app.route('/api/cryptopanic')
def api_panic():
    url = NEWS_APIS[0]
    try:
        r = requests.get(url, timeout=5)
        j = r.json()
        items = []
        for n in j.get("results", []):
            items.append({
                "id": n.get("id"),
                "title": n.get("title"),
                "url": n.get("url"),
                "time": n.get("published_at"),
                "source": "cryptopanic"
            })
        return jsonify({"articles": items})
    except Exception as ex:
        return jsonify({"articles": []})

@app.route('/api/openai', methods=['POST'])
def openai_proxy():
    data = request.json
    try:
        openai.api_key = OPENAI_API_KEY
        resp = openai.ChatCompletion.create(
            model=data.get("model","gpt-4o"),
            messages=data["messages"],
            temperature=data.get("temperature",1.1),
            user="neurona"
        )
        return jsonify(resp)
    except Exception as ex:
        return jsonify({"error": str(ex)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
