// Анимация нейросети (фон)
const canvas = document.getElementById('bg'), ctx = canvas.getContext('2d');
let W, H, nodes;
function resize(){ W=canvas.width=window.innerWidth; H=canvas.height=window.innerHeight; }
window.addEventListener('resize', resize);
function init(){
  nodes = Array.from({length:28}).map(_=>({
    x:Math.random()*W, y:Math.random()*H,
    vx:(Math.random()-.5)*.7, vy:(Math.random()-.5)*.7
  }));
}
function draw(){
  ctx.clearRect(0,0,W,H);
  ctx.lineCap='round'; ctx.lineJoin='round';
  nodes.forEach((a,i)=>{
    nodes.slice(i+1).forEach(b=>{
      const dx=a.x-b.x, dy=a.y-b.y, d=Math.hypot(dx,dy);
      if(d<220){
        ctx.strokeStyle=`rgba(0,0,0,${Math.min(0.35,(220-d)/170)})`;
        ctx.lineWidth=2.1;
        ctx.beginPath(); ctx.moveTo(a.x,a.y); ctx.lineTo(b.x,b.y); ctx.stroke();
      }
    });
  });
  nodes.forEach(n=>{
    n.x+=n.vx; n.y+=n.vy;
    if(n.x<0||n.x>W) n.vx*=-1;
    if(n.y<0||n.y>H) n.vy*=-1;
    ctx.fillStyle='rgba(0,0,0,.91)';
    ctx.beginPath(); ctx.arc(n.x,n.y,3.7,0,Math.PI*2); ctx.fill();
  });
  requestAnimationFrame(draw);
}
resize(); init(); draw();

// Глобальные переменные
let notifEnabled = localStorage.getItem('neurona_notif') === 'on';
let lastNewsIds = [];
const newsWindow = document.getElementById('newsWindow');
const chatWindow = document.getElementById('chatWindow');
const notifPopup = document.getElementById('notifPopup');
const notifBtn = document.getElementById('notifBtn');
const bellOn = document.getElementById('bell-on');
const bellOff = document.getElementById('bell-off');

// Включение/выключение уведомлений
function updateBellIcon() {
  if (notifEnabled) { bellOn.style.display=''; bellOff.style.display='none'; }
  else { bellOn.style.display='none'; bellOff.style.display=''; }
}
notifBtn.onclick = async () => {
  notifEnabled = !notifEnabled;
  localStorage.setItem('neurona_notif', notifEnabled ? 'on' : 'off');
  updateBellIcon();
  if (notifEnabled && 'Notification' in window) {
    let res = await Notification.requestPermission();
    if (res === "granted") showNotif("Уведомления включены");
    else showNotif("Нет разрешения на уведомления",true);
  }
  else if (!notifEnabled) showNotif("Уведомления отключены",true);
};
updateBellIcon();

// Отображение popup-уведомления
function showNotif(text, err) {
  notifPopup.textContent = text;
  notifPopup.style.background = err ? "#f33" : "#121";
  notifPopup.classList.add('show');
  setTimeout(()=>notifPopup.classList.remove('show'), 1650);
}

// ——— NEWS: Автоматическая подгрузка раз в 50 сек, свежие сверху ———
async function fetchNews() {
  try {
    let res = await fetch('/api/news');
    let js = await res.json();
    let news = (js.articles||[]).sort((a,b)=>
      new Date(b.time||b.published_at||0) - new Date(a.time||a.published_at||0)
    );
    // Показывать свежие сверху
    let html = news.slice(0,10).map(n => `
      <div class="news-item">
        <div class="news-item-title"><a href="${n.url}" target="_blank">${n.title}</a></div>
        <div class="news-item-meta">${n.time||n.published_at||''} <span style="color:#777;font-size:.89em;">[${n.source||''}]</span></div>
        ${n.impact? `<div style="font-size:.97em;color:#157;">Влияние: <b>${n.impact}</b></div>` : ""}
      </div>
    `).join('');
    newsWindow.innerHTML = html || '<div style="color:#888;">Нет новостей</div>';
    // Push notification по новым новостям
    if (notifEnabled && 'Notification' in window && Notification.permission === "granted") {
      news.forEach(n => {
        if (!lastNewsIds.includes(n.id||n.url)) {
          new Notification('📰 КриптоНОВОСТЬ', {body:n.title, icon:"https://i.ibb.co/XfKRzvcy/27.png", data:{url:n.url}});
          lastNewsIds.push(n.id||n.url);
        }
      });
      if (lastNewsIds.length > 16) lastNewsIds = lastNewsIds.slice(-16);
    }
  } catch(e){
    newsWindow.innerHTML = '<div style="color:#d44;">Ошибка новостного API</div>';
  }
}
// ——— CHAT: ИИ-комментарии и автосигналы ———
async function fetchAI() {
  try {
    let res = await fetch('/api/comment');
    let js = await res.json();
    let arr = (js.comments||[]).sort((a,b)=>b.time.localeCompare(a.time));
    let html = arr.map(m=>
      `<div class="message-bot">
        <div>${m.text.replace(/\n/g,'<br>')}</div>
        <div class="message-time">${m.time}</div>
      </div>`
    ).join('');
    chatWindow.innerHTML = html || '<div style="color:#888;">Нет сигналов</div>';
    // Добавить анимацию typing (трех точек) если бот думает
    if(js.typing) {
      chatWindow.innerHTML += `
      <div class="message-bot">
        <span class="typing-dots">
          <span class="tdot tdot1"></span>
          <span class="tdot tdot2"></span>
          <span class="tdot tdot3"></span>
        </span>
      </div>`;
    }
    chatWindow.scrollTop = chatWindow.scrollHeight;
  } catch(e){
    chatWindow.innerHTML = '<div style="color:#d44;">Ошибка комментариев ИИ</div>';
  }
}
// ——— Автообновление раз в 60 сек ———
function autoUpdate() {
  fetchNews(); fetchAI();
  setInterval(fetchNews, 57000);
  setInterval(fetchAI, 47000);
}
window.addEventListener('DOMContentLoaded', autoUpdate);

// Сервис-воркер (PWA + push)
if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js');
