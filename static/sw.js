self.addEventListener('install', e=>self.skipWaiting());
self.addEventListener('activate', e=>self.clients.claim());
self.addEventListener('fetch', e=>{
  e.respondWith(
    caches.open('static').then(cache=>
      cache.match(e.request).then(resp=>
        resp || fetch(e.request).then(response=>{
          cache.put(e.request, response.clone());
          return response;
        })
      )
    )
  );
});
