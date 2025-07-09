self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => self.clients.claim());
self.addEventListener('fetch', () => {});
self.addEventListener('push', function(event) {
  const data = event.data ? event.data.json() : {};
  event.waitUntil(
    self.registration.showNotification(
      data.title || "NEURONA Trade AI", 
      {
        body: data.body || "",
        icon: data.icon || "https://i.ibb.co/XfKRzvcy/27.png",
        badge: data.icon || "https://i.ibb.co/XfKRzvcy/27.png",
        data: data.url ? { url: data.url } : {}
      }
    )
  );
});
self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  if (event.notification.data && event.notification.data.url) {
    event.waitUntil(clients.openWindow(event.notification.data.url));
  }
});
