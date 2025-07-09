<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"/>
  <title>NEURONA | Trade AI Bot</title>
  <link rel="manifest" href="manifest.json">
  <link rel="icon" type="image/png" href="https://i.ibb.co/XfKRzvcy/27.png">
  <style>
    body { margin:0; font-family:Arial,sans-serif; background:#fff; color:#000; }
    .header {
      display:flex; align-items:center; gap:18px; padding:21px 18px 0 22px; min-height:68px;
    }
    .logo { width:40px; height:40px; margin-right:4px; }
    .title-box { display:flex; flex-direction:column; }
    .main-title { font-size:2.0rem; font-weight:bold; letter-spacing:.11em; }
    .sub-title { font-size:1.07rem; color:#888; font-weight:500; margin-top:-3px; }
    .refresh-btn {
      margin-left:auto; margin-right:8px; width:43px; height:43px;
      display:flex; align-items:center; justify-content:center;
      border:none; border-radius:100%; background:#fff; box-shadow:0 2px 8px #0001;
      cursor:pointer; transition:background .17s; font-size:2.15rem;
    }
    .refresh-btn:hover { background:#f4f6f8; }
    .refresh-btn svg { display:block; width:27px; height:27px; stroke-width:3.4px; color:#111;}
    .dialog {
      margin:65px auto 0; max-width:440px; min-width:270px; background:#fff;
      border-radius:18px; box-shadow:0 5px 28px #d0d2df33;
      padding:26px 22px 30px 22px; min-height:110px; transition:box-shadow .17s;
      display:flex; flex-direction:column; align-items:center;
    }
    .msg { margin:0 0 16px 0; min-width:90px; font-size:1.13rem; }
    .msg.signal {
      border-radius:12px; background:#eafdeb; border:1.2px solid #b5efc1;
      box-shadow:0 1px 5px #ccc3; color:#048800; font-size:1.12rem;
      padding:12px 14px; margin-bottom:12px;
    }
    .msg.signal.short { background:#fdecec; border:1.2px solid #f2b1b1; color:#d00000; }
    .msg.signal .price { color:#111; font-weight:700; }
    .msg.signal .tp, .msg.signal .sl { font-weight:600; }
    .msg.signal .tp { color:#238a2b; }
    .msg.signal .sl { color:#d00000; }
    .msg.ai, .msg.news {
      background:#f4f4fc; border-radius:10px; padding:8px 12px; color:#222; font-size:1rem; margin-bottom:7px;
    }
    .msg.news { background:#fef6de; }
    .typing { margin-top:12px; color:#888; }
    .dots { display:inline-flex; gap:3px; }
    .dot { width:7px; height:7px; border-radius:50%; background:#bbb; animation:bounce 1.1s infinite; }
    .dot2 { animation-delay:.22s; }
    .dot3 { animation-delay:.39s; }
    @keyframes bounce { 0%,80%,100%{ transform:translateY(0);} 35%{ transform:translateY(-8px);} }
    .error { background:#f4f6fa; border-radius:8px; padding:10px 14px; color:#466; font-size:1.03rem;}
    @media(max-width:600px){.dialog{max-width:96vw;min-width:0;}}
  </style>
</head>
<body>
  <div class="header">
    <img src="https://i.ibb.co/XfKRzvcy/27.png" class="logo" alt="NEURONA"/>
    <div class="title-box">
      <span class="main-title">NEURONA</span>
      <span class="sub-title">Trade AI Bot</span>
    </div>
    <button class="refresh-btn" id="refreshBtn" title="Обновить">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path d="M4.05 11a9 9 0 1 1 2.13 5.84" stroke-linecap="round"/>
        <path d="M4 4v7h7" stroke-linecap="round"/>
      </svg>
    </button>
  </div>
  <div class="dialog" id="dialog">
    <div class="msg typing" id="loading">
      <span>Загрузка...</span>
      <span class="dots"><span class="dot"></span><span class="dot dot2"></span><span class="dot dot3"></span></span>
    </div>
  </div>
  <script>
    const dialog = document.getElementById('dialog');
    const loading = document.getElementById('loading');
    const refreshBtn = document.getElementById('refreshBtn');

    function showTyping() {
      loading.style.display = "flex";
      loading.innerHTML = '<span>Загрузка...</span><span class="dots"><span class="dot"></span><span class="dot dot2"></span><span class="dot dot3"></span></span>';
    }
    function hideTyping() { loading.style.display = "none"; }
    function showError(msg) {
      dialog.innerHTML = `<div class="error">${msg}</div>`;
    }
    function colorText(text, color) {
      return `<span style="color:${color};font-weight:600;">${text}</span>`;
    }

    async function fetchFeed() {
      let r = await fetch("https://tradeneurona-7da73bd0c5bb.herokuapp.com/api/feed").then(r=>r.json());
      let s = r.signal, news = r.news, ai = r.ai;
      let cls = s.type == "LONG" ? "" : "short";
      let signal = `
        <div class="msg signal ${cls}">
          <b>BTC/USDT ${s.type=="LONG"?colorText("LONG","green"):colorText("SHORT","red")}</b>
          <br>Вход: <span class="price">${s.entry}</span> | 24ч: ${s.change}
          <br>Объём покупок: ${s.buyVol}, продаж: ${s.sellVol}
          <br>TP: <span class="tp">${s.tp}$</span> | SL: <span class="sl">${s.sl}$</span>
          <br>Min TP: <b>${s.tpMin}$</b> | Max TP: <b>${s.tpMax}$</b>
        </div>
        <div class="msg ai">AI-комментарий: <b>${ai}</b></div>
        <div class="msg news">Новость: <b>${news.title}</b> <br><a href="${news.url}" target="_blank">${news.url}</a></div>
      `;
      dialog.innerHTML = signal;
    }

    async function showAll() {
      showTyping();
      try {
        await fetchFeed();
      } catch (e) {
        showError("Ошибка загрузки данных с сервера.");
      }
    }

    refreshBtn.onclick = showAll;
    window.onload = showAll;

    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('sw.js');
    }
  </script>
</body>
</html>
