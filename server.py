import os
import requests
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def get_price():
    try:
        # CoinGecko open API
        cg = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd').json()
        price = cg['bitcoin']['usd']
        # 24h data
        m = requests.get('https://api.coingecko.com/api/v3/coins/bitcoin?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false&sparkline=false').json()
        chg = m['market_data']['price_change_percentage_24h']
        vol = m['market_data']['total_volume']['usd']
        time = m['last_updated']
        return price, chg, vol, time
    except Exception as e:
        return '-', '-', '-', '-'

@app.route('/api/signal')
def api_signal():
    price, chg, vol, time = get_price()
    # Fake AI signal (логика под себя)
    direction = "LONG" if float(chg) > 0 else "SHORT"
    comment = f"Сигнал: {direction}, 24ч: {chg}%"
    signal = {
        "price": price,
        "change": chg,
        "volume": vol,
        "direction": direction,
        "comment": comment,
        "time": time
    }
    return jsonify({"signal": signal})

@app.route('/api/news')
def api_news():
    try:
        # CryptoPanic public RSS feed (json proxy)
        r = requests.get('https://cryptopanic.com/api/v1/posts/?auth_token=YOUR_TOKEN&currencies=BTC&public=true')
        j = r.json()
        news = []
        for item in j.get('results', []):
            title = item['title']
            url = item['url']
            source = item['source']['title']
            published = item['published_at'][11:16]
            news.append({"title": title, "url": url, "source": source, "time": published})
        return jsonify({"news": news[:7]})
    except Exception as e:
        # Фейк если ошибка
        return jsonify({"news": [
            {"title": "Crypto news недоступны", "url": "#", "source": "n/a", "time": "--:--"}
        ]})

@app.route('/')
def root(): return app.send_static_file('index.html')
@app.route('/<path:path>')
def static_proxy(path): return app.send_static_file(path)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
