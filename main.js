const newsPane = document.getElementById('news-pane');
const signalsPane = document.getElementById('signals-pane');
const notifPopup = document.getElementById('notifPopup');
const notifPopupMsg = document.getElementById('notifPopupMsg');

// --- Canvas BG
let bg = document.getElementById("bg");
if (bg) {
  let ctx = bg.getContext("2d");
  function resize() {
    bg.width = window.innerWidth;
    bg.height = window.innerHeight;
  }
  window.addEventListener('resize', resize);
  resize();
  let points = Array.from({length: 24}, ()=>({
    x: Math.random()*bg.width,
    y: Math.random()*bg.height,
    vx: (Math.random()-0.5)*.7,
    vy: (Math.random()-0.5)*.7
  }));
  function drawBG() {
    ctx.clearRect(0,0,bg.width,bg.height);
    for(let i=0;i<points.length;i++) {
      let p=points[i];
      p.x+=p.vx; p.y+=p.vy;
      if (p.x<0||p.x>bg.width) p.vx*=-1;
      if (p.y<0||p.y>bg.height) p.vy*=-1;
      ctx.beginPath();
      ctx.arc(p.x,p.y,3,0,2*Math.PI);
      ctx.fillStyle="#191919";
      ctx.fill();
      for(let j=i+1;j<points.length;j++) {
        let q=points[j],d=Math.hypot(p.x-q.x,p.y-q.y);
        if(d<150){
          ctx.beginPath();
          ctx.moveTo(p.x,p.y);
          ctx.lineTo(q.x,q.y);
          ctx.strokeStyle="rgba(30,30,30,"+((150-d)/150*0.29)+")";
          ctx.lineWidth=1.1;
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(drawBG);
  }
  drawBG();
}

// Push notification
function showNotif(msg) {
  notifPopupMsg.innerHTML = msg;
  notifPopup.classList.add("active");
  setTimeout(()=>notifPopup.classList.remove("active"),2800);
}

// --- NEWS
let lastNewsIds = [];
async function fetchNews() {
  let r = await fetch('/api/news');
  let data = await r.json();
  let news = data.articles || [];
  let html = '';
  let shownIds = [];
  for (let n of news) {
    let title = n.title || '';
    let url = n.url || '#';
    let time = n.time ? n.time.replace('T',' ').slice(0,16) : '';
    let source = n.source ? n.source.replace(/^www\./, '').split('.')[0] : '';
    shownIds.push(n.id || title+url);
    html += `
    <div class="news-item" onclick="window.open('${url}','_blank')">
      <a class="news-title" href="${url}" target="_blank">${title}</a>
      <div class="news-meta">
        <span class="news-source">${source}</span>
        <span>${time}</span>
      </div>
    </div>`;
  }
  newsPane.innerHTML = html;
  if (lastNewsIds.length && shownIds[0] !== lastNewsIds[0]) {
    showNotif('📰 Новость: ' + news[0].title);
    if (window.Notification && Notification.permission === "granted")
      new Notification("NEURONA: Новая новость", { body: news[0].title, icon: "https://i.ibb.co/XfKRzvcy/27.png"});
  }
  lastNewsIds = shownIds;
}
fetchNews();
setInterval(fetchNews, 60000);

// --- СИГНАЛЫ/АНАЛИТИКА с backend
async function fetchSignals() {
  let r = await fetch('/api/signal');
  let data = await r.json();
  let s = data.signal || {};
  let html = `
    <div class="news-item" style="font-weight:600;color:${s.direction=='LONG'?'#1d9a3a':'#d13a3a'};">
      <div class="news-title">${s.symbol} ${s.direction} <span style="color:#888;font-size:0.95em">(${s.confidence||'AI'})</span></div>
      <div class="news-meta">
        <span class="news-source">binance</span>
        <span>${s.time || ''}</span>
      </div>
      <div style="color:#666;font-size:.98rem;margin-top:3px">
        Цена: $${s.price||'-'}<br>
        24ч объём: ${s.volume||'-'} BTC<br>
        Изменение 24ч: ${s.change||'-'}%<br>
        Верх стакана: ${s.orderbook_top||'-'}<br>
        Низ стакана: ${s.orderbook_bottom||'-'}<br>
        <b>AI:</b> ${s.comment||''}
      </div>
    </div>
  `;
  signalsPane.innerHTML = html;
}
fetchSignals();
setInterval(fetchSignals, 65000);

if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js');
if (window.Notification && Notification.permission !== "granted")
  Notification.requestPermission();
