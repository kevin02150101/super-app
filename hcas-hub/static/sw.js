// HCAS Hub service worker — minimal pass-through (no offline cache yet).
// Exists so navigator.serviceWorker.register('/static/sw.js') doesn't 404.

self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

// No fetch handler → browser uses default network behavior.
