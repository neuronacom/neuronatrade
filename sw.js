self.addEventListener("install", function(e) {
  self.skipWaiting();
});
self.addEventListener("activate", function(e) {
  e.waitUntil(self.clients.claim());
});
self.addEventListener("fetch", function(e) {
  e.respondWith(fetch(e.request));
});
self.addEventListener("push", function(event) {
  const data = event.data.json();
  const title = data.title || "NEURONA Update";
  const options = {
    body: data.body || "Новое обновление доступно!",
    icon: "https://i.ibb.co/XfKRzvcy/27.png",
    badge: "https://i.ibb.co/XfKRzvcy/27.png",
    data: { url: data.url || "/" }
  };
  event.waitUntil(self.registration.showNotification(title, options));
});
self.addEventListener("notificationclick", function(event) {
  event.notification.close();
  if (event.notification.data && event.notification.data.url)
    clients.openWindow(event.notification.data.url);
});
