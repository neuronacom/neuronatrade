let signalTimer = null, newsTimer = null;

async function fetchSignal() {
  document.getElementById('ai-signal').innerHTML = 'Загрузка...';
  try {
    let res = await fetch('/api/signal');
    let js = await res.json();
    let s = js.signal;
    document.getElementById('ai-signal').innerHTML = `
      <b>BTC/USDT</b> - (AI)<br>
      <a href="https://binance.com" target="_blank" style="color:#164eff;text-decoration:underline;">binance</a> -
      <br>Цена: $${s.price ?? '-'}
      <br>24ч объём: ${s.volume ?? '-'} BTC
      <br>Изменение 24ч: ${s.change ?? '-'}%
      <br>Верх стакана: ${s.orderbook_top ?? '-'}
      <br>Низ стакана: ${s.orderbook_bottom ?? '-'}
      <br><b>AI:</b> ${s.comment}
      <br><span style="font-size:0.96em;color:#bbb;">${s.time ?? ''}</span>
    `;
    showPush('AI сигнал BTC: ' + s.direction + ', $' + s.price + ' — ' + s.comment);
  } catch (e) {
    document.getElementById('ai-signal').innerHTML = 'Ошибка API: ' + e;
  }
}

async function fetchNews() {
  document.getElementById('news-list').innerHTML = 'Загрузка...';
  try {
    let res = await fetch('/api/news');
    let js = await res.json();
    let list = js.news.map(n => `
      <div class="news-item">
        <a href="${n.url}" target="_blank" class="news-title">${n.title}</a>
        <span class="news-src">${n.source}</span>
        <span class="news-time">${n.time}</span>
      </div>
    `).join('');
    document.getElementById('news-list').innerHTML = list;
    showPush('Новая новость: ' + (js.news[0]?.title ?? '...'));
  } catch (e) {
    document.getElementById('news-list').innerHTML = 'Ошибка API: ' + e;
  }
}

// PUSH уведомления (браузер + pop-up)
let notifActive = false;
function showPush(msg) {
  if (notifActive && 'Notification' in window && Notification.permission === 'granted') {
    new Notification(msg);
  }
  let np = document.getElementById('notifPopup');
  if (np) {
    np.innerText = msg;
    np.style.display = 'block';
    setTimeout(() => { np.style.display = 'none'; }, 4200);
  }
}
document.getElementById('push-btn').onclick = function() {
  if (!notifActive && 'Notification' in window) {
    Notification.requestPermission().then(p => {
      if (p === "granted") {
        notifActive = true;
        this.classList.add('active');
        showPush('Уведомления включены');
      }
    });
  } else {
    notifActive = false;
    this.classList.remove('active');
    showPush('Уведомления отключены');
  }
};

function animateDots() {
  let canvas = document.getElementById('bg');
  let ctx = canvas.getContext('2d');
  let w = window.innerWidth, h = window.innerHeight;
  canvas.width = w; canvas.height = h;
  let pts = [];
  for (let i = 0; i < 22; ++i) {
    pts.push({x: Math.random()*w, y: Math.random()*h, dx: (Math.random()-0.5)*0.6, dy: (Math.random()-0.5)*0.6});
  }
  function draw() {
    ctx.clearRect(0,0,w,h);
    for (let i=0; i<pts.length; ++i) {
      let p = pts[i];
      p.x += p.dx; p.y += p.dy;
      if (p.x < 0 || p.x > w) p.dx *= -1;
      if (p.y < 0 || p.y > h) p.dy *= -1;
      ctx.beginPath();
      ctx.arc(p.x, p.y, 3, 0, 2*Math.PI); ctx.fillStyle="#111"; ctx.fill();
      for (let j=i+1; j<pts.length; ++j) {
        let d = Math.hypot(p.x-pts[j].x, p.y-pts[j].y);
        if (d < 140) {
          ctx.beginPath();
          ctx.moveTo(p.x, p.y); ctx.lineTo(pts[j].x, pts[j].y);
          ctx.strokeStyle = "rgba(10,10,10,0.09)";
          ctx.lineWidth = 1.2; ctx.stroke();
        }
      }
    }
    requestAnimationFrame(draw);
  }
  draw();
}
window.onload = () => {
  animateDots();
  fetchSignal(); fetchNews();
  signalTimer = setInterval(fetchSignal, 62000);
  newsTimer = setInterval(fetchNews, 60000);
};
window.onresize = animateDots;
