// 這個版本會清掉舊的快取，並取消註冊自己，讓網站恢復成每次都讀取最新檔案
self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.map((key) => caches.delete(key)))
    ).then(() => self.registration.unregister())
     .then(() => self.clients.matchAll())
     .then((clients) => {
       clients.forEach((client) => client.navigate(client.url));
     })
  );
});
