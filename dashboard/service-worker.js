const CACHE_NAME = "sentinel-shell-v6";
const SHELL = [
  "/dashboard/",
  "/dashboard/index.html",
  "/dashboard/manifest.json",
  "/dashboard/icon.svg",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // Network-first for API calls (anything not under /dashboard shell).
  const isApi = url.pathname.startsWith("/telegraph/") ||
                url.pathname.startsWith("/risk") ||
                url.pathname.startsWith("/health") ||
                url.pathname.startsWith("/receipts") ||
                url.pathname.startsWith("/scoreboard") ||
                url.pathname.startsWith("/cities") ||
                url.pathname.startsWith("/diseases") ||
                url.pathname.startsWith("/alerts");

  if (isApi) {
    event.respondWith(
      fetch(req).catch(() =>
        new Response(JSON.stringify({ offline: true, error: "offline" }), {
          status: 503,
          headers: { "Content-Type": "application/json" },
        })
      )
    );
    return;
  }

  // Cache-first for shell assets.
  event.respondWith(
    caches.match(req).then((cached) => {
      if (cached) return cached;
      return fetch(req).then((res) => {
        if (res && res.status === 200 && req.method === "GET") {
          const copy = res.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(req, copy));
        }
        return res;
      }).catch(() => caches.match("/dashboard/index.html"));
    })
  );
});