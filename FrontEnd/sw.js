const CACHE_NAME = 'open-air-cache-v3';

// Pre-cache essential files on install
self.addEventListener("install", e => {
  self.skipWaiting(); // Force the waiting service worker to become the active service worker
  e.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll([
        "./",
        "./index.html",
        "./manifest.json",
        "./assets/icon-192.png",
        "./assets/icon-512.png"
      ]);
    })
  );
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cache => {
          if (cache !== CACHE_NAME) {
            return caches.delete(cache);
          }
        })
      );
    })
  );
});

// Network-First Strategy with Cache Fallback
self.addEventListener("fetch", e => {
  // Only intercept GET requests
  if (e.request.method !== "GET") return;

  // Don't cache browser-sync or socket connections
  if (e.request.url.includes('/socket.io/') || e.request.url.includes('ws://') || e.request.url.includes('wss://')) return;

  e.respondWith(
    fetch(e.request)
      .then(networkResponse => {
        // Only cache successful responses (allow opaque responses from CDNs too)
        if (networkResponse && (networkResponse.status === 200 || networkResponse.status === 0)) {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then(cache => {
            cache.put(e.request, responseToCache);
          });
        }
        return networkResponse;
      })
      .catch(() => {
        // If network fetch fails (offline), return the cached version
        return caches.match(e.request);
      })
  );
});
