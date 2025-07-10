import os
import requests
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

app = Flask(__name__, static_folder='static')
CORS(app)

BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY", "")
BINANCE_SECRET = os.environ.get("BINANCE_SECRET", "")
CRYPTOPANIC_API_KEY = os.environ.get("CRYPTOPANIC_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

def get_binance_btc_data():
    # Binance заблокирован на Heroku, поэтому возвращаем "-"
    return {
        "bids": [],
        "asks": [],
        "lastPrice": None,
        "volume": None,
        "priceChangePercent": None
    }

def get_cryptopanic_news():
    try:
        url = f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTOPANIC_API_KEY}&currencies=BTC&public=true"
        resp = requests.get(url)
        news = resp.json()
        results = news.get('results', [])
        # Берём только первую новость
        if results:
            n = results[0]
            return [{
                "title": n.get('title', ''),
                "desc": n.get('description', ''),
                "published_at": n.get("published_at", '')[11:16]
            }]
        else:
            return []
    except Exception as e:
        print("CryptoPanic ERROR:", e, flush=True)
        return []

def translate_to_russian(text):
    try:
        import openai
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        messages = [
            {"role": "system", "content": "Ты переводчик с английского на русский. Переводи только текст, без пояснений и примечаний."},
            {"role": "user", "content": text}
        ]
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=350
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("TRANSLATE ERROR:", e, flush=True)
        return text

def ai_btc_signal(news):
    try:
        import openai
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        last_news = news[0]['title'] + ". " + news[0]['desc'] if news else ""
        messages = [
            {"role": "system", "content": "Ты профессиональный трейдер криптовалют. На основе новостей дай краткий сигнал по BTC/USDT: LONG, SHORT, HOLD. Пример: 'Сигнал: LONG от 58900, SL 58000, TP 60000. Комментарий: ...'. Без стаканов и объёмов. Только на русском языке!"},
            {"role": "user", "content": f"Актуальные новости: {last_news}"}
        ]
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=350
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("OPENAI ERROR:", e, flush=True)
        return "Ошибка AI: " + str(e)

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/static/<path:path>")
def static_files(path):
    return send_from_directory("static", path)

@app.route("/api/data")
def api_data():
    btc = get_binance_btc_data()
    news = get_cryptopanic_news()
    # Переводим новость на русский
    for n in news:
        n['title'] = translate_to_russian(n['title'])
        if n['desc']:
            n['desc'] = translate_to_russian(n['desc'])
    return jsonify({"btc": btc, "news": news})

@app.route("/api/signal")
def api_signal():
    news = get_cryptopanic_news()
    signal = ai_btc_signal(news)
    return jsonify({"signal": signal})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
