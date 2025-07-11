import os
import requests
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime, timezone, timedelta
import openai
import time
import re

app = Flask(__name__, static_folder="static")
CORS(app)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

CACHE = {
    "signals": [],
    "news": [],
    "last_ts": 0,
    "last_price": None,
    "last_news_id": None,
    "last_orderbook": None,
    "last_ai_full": "",
}

def get_time(ts=None):
    tz = timezone(timedelta(hours=3))  # Kyiv
    dt = datetime.fromtimestamp(ts or time.time(), tz)
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

def get_cryptocompare_news():
    try:
        url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
        r = requests.get(url, timeout=5)
        arr = []
        for a in r.json().get("Data", [])[:8]:
            arr.append({
                "id": a["id"],
                "title": a["title"][:120],
                "url": a["url"],
                "time": datetime.fromtimestamp(a.get("published_on", 0)).strftime("%H:%M")
            })
        return arr
    except Exception as ex:
        print("CRYPTOCOMPARE ERROR:", ex)
        return []

def translate_text(text):
    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": f"Переведи это на русский кратко и понятно:\n\n{text}"}
            ],
            temperature=0.15,
            max_tokens=140,
        )
        return completion.choices[0].message.content
    except Exception as ex:
        print("TRANSLATE ERROR:", ex)
        return text

def parse_signal(text):
    # Извлекаем из текста четкие параметры сигнала
    result = {
        "type": "",
        "timeframe": "",
        "entry": "",
        "tp": "",
        "sl": "",
        "reason": ""
    }
    # Тип сигнала
    match_type = re.search(r'\b(LONG|SHORT|HODL|ЛОНГ|ШОРТ)\b', text.upper())
    if match_type:
        t = match_type.group(1).upper()
        result["type"] = "LONG" if t in ['LONG', 'ЛОНГ'] else ("SHORT" if t in ['SHORT', 'ШОРТ'] else "HODL")
    # Таймфрейм
    match_tf = re.search(r'Таймфрейм[^\w:]*:?[\s\-]*([^\n,\.]+)', text, re.IGNORECASE)
    if match_tf:
        result["timeframe"] = match_tf.group(1).strip()
    # Вход
    match_entry = re.search(r'Вход[^\w:]*:?[\s\-]*([\d\.,]+)', text, re.IGNORECASE)
    if match_entry:
        result["entry"] = match_entry.group(1).strip()
    # TP
    match_tp = re.search(r'(Тейк.?профит|TP)[^\w:]*:?[\s\-]*([\d\.,]+)', text, re.IGNORECASE)
    if match_tp:
        result["tp"] = match_tp.group(2).strip()
    # SL
    match_sl = re.search(r'(Стоп.?лосс|SL)[^\w:]*:?[\s\-]*([\d\.,]+)', text, re.IGNORECASE)
    if match_sl:
        result["sl"] = match_sl.group(2).strip()
    # Причина
    match_reason = re.search(r'(Почему|AI.?комментарий)[^\n:]*:?[\s\-]*(.+)', text, re.IGNORECASE)
    if match_reason:
        result["reason"] = match_reason.group(2).strip()
    # Fallback для причины
    if not result["reason"]:
        # берем последний абзац
        blocks = [b.strip() for b in text.split('\n') if b.strip()]
        if blocks:
            result["reason"] = blocks[-1]
    return result

def gen_ai_signal(price, ob, news, full=False):
    news_titles = [n['title'] for n in news[:3]]
    tf = "5m/15m/1h"
    prompt = f"""
Ты — криптоаналитик-бот NEURONA. Дай только один четкий проверенный торговый сигнал по BTC/USDT для фьючерсов на основе стакана Binance (bid: {ob['bids']}, ask: {ob['asks']}), текущей цены {price}.

Строгая структура ответа:
1. Таймфрейм: (например: 5m, 15m, 1h)
2. Сигнал: LONG, SHORT или HODL.
3. Вход (Entry): четкая цена.
4. Тейк-профит (TP): четкая цена.
5. Стоп-лосс (SL): четкая цена.
6. Почему: 1-2 предложения — причина сигнала, основываясь на новостях, стакане и цене (без воды, только суть, не повторяй структуру).

Не пиши дополнительные комментарии, анализы и рассуждения вне этих пунктов.
Пиши только по-русски, максимально понятно, без воды.

Пример формата:
Таймфрейм: 15m
Сигнал: LONG
Вход: 61750
Тейк-профит: 62500
Стоп-лосс: 61300
Почему: Цена отбилась от поддержки, объемы растут, новости позитивные.
"""
    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.13,
            max_tokens=200,
        )
        content = completion.choices[0].message.content.strip()
        # Разбор по структуре
        parsed = parse_signal(content)
        parsed["text"] = content
        parsed["time"] = get_time()
        return parsed
    except Exception as e:
        print("OPENAI ERROR:", e)
        return {
            "type": "HODL",
            "timeframe": "",
            "entry": "",
            "tp": "",
            "sl": "",
            "reason": "Анализ временно недоступен.",
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
    news = get_cryptocompare_news()
    for n in news:
        n['title'] = translate_text(n['title'])

    # Стартовый (полный) AI-анализ только при первом заходе (или старте приложения)
    if not CACHE["last_ai_full"]:
        ai_full = gen_ai_signal(price, ob, news, full=True)
        CACHE["last_ai_full"] = ai_full["text"]
        CACHE["signals"].append(ai_full)
        CACHE["signals"] = CACHE["signals"][-10:]
        CACHE["last_price"] = price
        CACHE["last_orderbook"] = ob
        CACHE["last_ts"] = now
        CACHE["news"] = news[:8]

    # Обычный сигнал — только если что-то изменилось
    elif (
        CACHE['last_price'] != price
        or CACHE['last_orderbook'] != ob
        or (news and news[-1]['id'] != (CACHE['news'][-1]['id'] if CACHE['news'] else None))
    ):
        ai_signal = gen_ai_signal(price, ob, news, full=False)
        CACHE["signals"].append(ai_signal)
        CACHE["signals"] = CACHE["signals"][-10:]
        CACHE['last_price'] = price
        CACHE['last_orderbook'] = ob
        CACHE["news"] = news[:8]
        CACHE["last_ts"] = now

    # Ответ
    return jsonify({
        "signals": CACHE["signals"][-5:],   # Верхнее окно — только сигналы/комменты
        "news": CACHE["news"][:6]           # Нижнее окно — новости
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
