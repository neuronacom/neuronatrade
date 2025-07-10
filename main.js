let notifEnabled = false;

function showNotif(msg) {
  let np = document.getElementById('notifPopup');
  np.innerHTML = msg;
  np.style.display = "block";
  setTimeout(() => { np.style.display = "none"; }, 3200);
}

// ---- Push notification logic ----
document.getElementById('push-btn').onclick = async function() {
  if (notifEnabled) {
    notifEnabled = false;
    document.getElementById('bell').style.display = '';
    document.getElementById('bell-off').style.display = 'none';
    showNotif("Уведомления выключены");
    return;
  }
  if (Notification && Notification.permission === "granted") {
    notifEnabled = true;
    document.getElementById('bell').style.display = 'none';
    document.getElementById('bell-off').style.display = '';
    showNotif("Уведомления включены!");
    return;
  }
  if (Notification && Notification.permission !== "denied") {
    Notification.requestPermission().then(function(permission) {
      if (permission === "granted") {
        notifEnabled = true;
        document.getElementById('bell').style.display = 'none';
        document.getElementById('bell-off').style.display = '';
        showNotif("Уведомления включены!");
      }
    });
  }
};

if ('serviceWorker' in navigator) {
  window.addEventListener('load', function() {
    navigator.serviceWorker.register('sw.js');
  });
}

function sendPush(title, body) {
  if (notifEnabled && Notification.permission === "granted") {
    new Notification(title, { body });
  }
}

// --- Animated bg (простая сеть точек)
const canvas = document.getElementById('bg');
if (canvas) {
  const ctx = canvas.getContext('2d');
  let w = window.innerWidth, h = window.innerHeight;
  canvas.width = w; canvas.height = h;
  let points = [];
  for (let i = 0; i < 24; ++i)
    points.push({x:Math.random()*w, y:Math.random()*h, dx:(Math.random()-.5)*.5, dy:(Math.random()-.5)*.6});
  function drawBg() {
    ctx.clearRect(0,0,w,h);
    for(let i=0;i<points.length;i++) {
      let p = points[i];
      p.x += p.dx; p.y += p.dy;
      if(p.x<0||p.x>w) p.dx*=-1;
      if(p.y<0||p.y>h) p.dy*=-1;
      ctx.beginPath(); ctx.arc(p.x,p.y,2.7,0,7); ctx.fillStyle="#111"; ctx.fill();
      for(let j=i+1;j<points.length;j++) {
        let q=points[j],dx=p.x-q.x,dy=p.y-q.y,d=Math.sqrt(dx*dx+dy*dy);
        if(d<180) {ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(q.x,q.y);ctx.strokeStyle="#bbb2";ctx.stroke();}
      }
    }
    requestAnimationFrame(drawBg);
  }
  drawBg();
}

// -- NEWS FETCH
async function fetchNews() {
  let el = document.getElementById('news-list');
  el.innerHTML = "Загрузка...";
  try {
    let r = await fetch('/api/news');
    let j = await r.json();
    el.innerHTML = "";
    (j.news||[]).forEach(item => {
      el.innerHTML += `
        <div class="news-item">
          <a class="news-link" href="${item.url}" target="_blank">${item.title}</a>
          <div class="news-meta">${item.source || ""} • ${item.time || ""}</div>
        </div>
      `;
    });
    if (notifEnabled && j.news && j.news[0])
      sendPush("BTC Новости", j.news[0].title);
  } catch(e) {
    el.innerHTML = "Нет новостей.";
  }
}

// -- AI SIGNAL FETCH
async function fetchSignal() {
  let el = document.getElementById('ai-signal');
  el.innerHTML = '<div class="typing"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>';
  try {
    let r = await fetch('/api/signal');
    let j = await r.json();
    let sig = j.signal;
    el.innerHTML = `
      <div class="ai-signal-line"><b>Цена:</b> $${sig.price} • <b>Объём 24ч:</b> $${sig.volume} • <b>Изм. 24ч:</b> ${sig.change}%</div>
      <b>AI:</b> ${sig.comment} <br>
      <b>Тренд:</b> ${sig.direction} <br>
      <b>Время:</b> ${sig.time.replace('T',' ').replace('Z','')}
    `;
    if (notifEnabled)
      sendPush("BTC Сигнал", sig.comment);
  } catch(e) {
    el.innerHTML = "Ошибка анализа AI.";
  }
}

window.onload = () => {
  fetchNews();
  fetchSignal();
  setInterval(fetchNews, 60000);
  setInterval(fetchSignal, 60000);
};
