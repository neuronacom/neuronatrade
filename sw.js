self.addEventListener('install', e=>self.skipWaiting());
self.addEventListener('activate', e=>self.clients.claim());
self.addEventListener('fetch', e=>{
  if(e.request.method==='GET')
    e.respondWith(caches.open('v1').then(cache=>
      cache.match(e.request).then(resp=>resp||fetch(e.request).then(r=>{
        cache.put(e.request,r.clone()); return r;
      }))
    ));
});
self.addEventListener('notificationclick', e=>{
  if(e.notification.data && e.notification.data.url)
    clients.openWindow(e.notification.data.url);
  e.notification.close();
});
