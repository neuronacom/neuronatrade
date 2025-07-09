const express = require('express');
const fetch = require('node-fetch');
const { Configuration, OpenAIApi } = require('openai');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 5000;

// Настройки OpenAI через переменную окружения Heroku
const configuration = new Configuration({
  apiKey: process.env.OPENAI_KEY,
});
const openai = new OpenAIApi(configuration);

// CryptoPanic (API-ключ хранится в Heroku)
const CRYPTOPANIC_KEY = process.env.CRYPTOPANIC_TOKEN;

app.use(express.static(path.join(__dirname)));

// Получение свежих новостей
app.get('/api/news', async (req, res) => {
  try {
    const url = `https://cryptopanic.com/api/developer/v2/posts/?auth_token=${CRYPTOPANIC_KEY}&public=true`;
    const response = await fetch(url);
    const json = await response.json();
    const articles = json.results.map(post => ({
      id: post.id,
      title: post.title,
      url: post.url,
      published: post.published_at
    }));
    res.json(articles);
  } catch (err) {
    console.error("Ошибка новостей:", err.message);
    res.status(500).json([]);
  }
});

// Получение сигнала от GPT-4o
app.get('/api/signals', async (req, res) => {
  try {
    const completion = await openai.createChatCompletion({
      model: "gpt-4o",
      messages: [
        {
          role: "system",
          content: `Ты — профессиональный трейдер. Дай точный сигнал по BTC/USDT: LONG или SHORT, только если есть 100% уверенность.
          
- Проанализируй стаканы, объёмы, график, индикаторы (RSI, MACD, EMA), настроение рынка, последние новости.
- Ответ строго в формате:
{
  "long": "Уверенный сигнал на LONG. Уровень входа: $XYZ, цель: $ABC, стоп: $DEF",
  "short": null
}
или наоборот. Не давай оба сразу.`
        },
        {
          role: "user",
          content: "Дай текущий сигнал по BTC/USDT"
        }
      ],
      temperature: 0.8
    });

    const raw = completion.data.choices[0].message.content.trim();
    const parsed = JSON.parse(raw);
    res.json(parsed);
  } catch (err) {
    console.error("Ошибка GPT:", err.message);
    res.status(500).json({ error: "AI error" });
  }
});

app.listen(PORT, () => {
  console.log(`NEURONA AI сервер запущен на порту ${PORT}`);
});
