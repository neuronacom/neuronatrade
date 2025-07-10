// Анимация точек/связей на фоне
(function animateBG(){
  let c = document.createElement('canvas');
  c.id = "bg"; document.getElementById("bg-animation").appendChild(c);
  let ctx = c.getContext('2d'), w=window.innerWidth, h=window.innerHeight;
  c.width = w; c.height = h;
  let points = Array.from({length:22},()=>({x:Math.random()*w,y:Math.random()*h}));
  function draw(){
    ctx.clearRect(0,0,w,h);
    points.forEach((p,i)=>{
      ctx.beginPath(); ctx.arc(p.x,p.y,2,0,2*Math.PI); ctx.fillStyle="#222"; ctx.fill();
      points.forEach((q,j)=>{if(i!==j&&Math.hypot(p.x-q.x,p.y-q.y)<180){
        ctx.beginPath(); ctx.moveTo(p.x,p.y); ctx.lineTo(q.x,q.y); ctx.strokeStyle="#8881"; ctx.stroke();
      }});
    });
  }
  setInterval(()=>{points.forEach(p=>{p.x+=Math.random()*3-1.5;p.y+=Math.random()*3-1.5;});draw();},100);
})();

function notif(msg) {
  let pop = document.getElementById('notifPopup');
  pop.innerHTML = msg; pop.classList.add('show');
  setTimeout(()=>pop.classList.remove('show'), 5200);
}

function requestPush() {
  if ('Notification' in window) {
    Notification.requestPermission().then(res=>{
      if(res==='granted') notif('🔔 Уведомления включены!');
      else notif('❌ Уведомления отключены');
    });
  }
}

let bell = document.getElementById('notifyBell');
bell.onclick = function() {
  bell.classList.toggle('off');
  if(!bell.classList.contains('off')) requestPush();
};

let latestSignal = "", latestNews = "";

// Загрузка новостей с сервера
function loadNews() {
  fetch('/api/news').then(r=>r.json()).then(d=>{
    let newsFeed = document.getElementById('newsFeed');
    if(!d.news || !d.news.length) { newsFeed.innerHTML='<div>Нет новостей</div>'; return;}
    newsFeed.innerHTML = d.news.map(n=>
      `<div class="news-item"><a href="${n.link}" target="_blank" class="news-link">${n.title}</a><span class="news-time">${n.time}</span></div>`
    ).join('');
    let top = d.news[0];
    if(top && top.title!==latestNews){
      latestNews=top.title;
      if(Notification.permission==="granted")
        new Notification("BTC новость", {body: top.title, icon:'/favicon.ico'});
    }
  });
}
loadNews(); setInterval(loadNews,60000);

// Загрузка AI сигнала с сервера
function loadSignal() {
  fetch('/api/signal').then(r=>r.json()).then(d=>{
    let aiFeed = document.getElementById('aiFeed');
    let msg = `<div class="ai-comment">${d.signal}</div>`;
    aiFeed.innerHTML = msg;
    if(d.signal!==latestSignal && Notification.permission==="granted")
      new Notification("AI BTC сигнал", {body:d.signal.slice(0,150), icon:'/favicon.ico'});
    latestSignal = d.signal;
  });
}
loadSignal(); setInterval(loadSignal,60000);
