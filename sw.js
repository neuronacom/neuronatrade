self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => self.clients.claim());

self.addEventListener('notificationclick', function(event) {
  let url = event.notification.data && event.notification.data.url;
  if (url) {
    event.notification.close();
    event.waitUntil(clients.openWindow(url));
  }
});
