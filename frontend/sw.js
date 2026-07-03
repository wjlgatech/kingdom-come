// Minimal service worker (B3): makes the app installable and keeps static
// assets warm. Deliberately tiny — pages and API stay network-only so the
// live data model (in-process state, streaming chat) is never masked by a
// stale cache. Bump the version to invalidate.
const CACHE = "kc-static-v1";

self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))),
    ),
  );
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  const isStatic = url.origin === self.location.origin && url.pathname.startsWith("/static/");
  if (!isStatic || event.request.method !== "GET") return; // network-only

  // Stale-while-revalidate for static assets.
  event.respondWith(
    caches.open(CACHE).then(async (cache) => {
      const cached = await cache.match(event.request);
      const refresh = fetch(event.request)
        .then((res) => {
          if (res.ok) cache.put(event.request, res.clone());
          return res;
        })
        .catch(() => cached);
      return cached || refresh;
    }),
  );
});
