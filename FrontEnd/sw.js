/**
 * Header: sw.js
 * Purpose: sw component or utility.
 * Description: Handles logic and rendering for sw component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// Bumped to v4: the activate handler deletes every cache whose name differs,
// so raising this number is how a stale precache gets evicted.
const CACHE_NAME = 'open-air-cache-v4';

// Never cache these — they are the app itself, not its assets.
//
// index.html names every widget by `?v=` URL, and the .jsx files are compiled
// in-browser by Babel. Serving either from cache means the page renders fresh
// panel JSON (fetched with a cache-buster) through old widget code, which does
// not look like a caching problem: it looks like an edit that did nothing. A
// lab tool served from localhost has nothing to gain from offline-caching its
// own source.
const NEVER_CACHE = /\.(jsx|html)(\?|$)|\/api\//;

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

  // Source and API: straight to the network, and force a revalidation so the
  // browser's own HTTP cache cannot serve a stale copy behind our back.
  // `mode: 'navigate'` covers the bare "/" that serves index.html.
  if (NEVER_CACHE.test(e.request.url) || e.request.mode === 'navigate') {
    e.respondWith(
      fetch(e.request, { cache: 'no-cache' }).catch(() => caches.match(e.request))
    );
    return;
  }

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
