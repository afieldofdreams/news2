// Minimal service worker. Its only job is to make the site installable
// on Chrome/Android (which requires a registered SW). No offline caching:
// every request goes straight to the network.
self.addEventListener("install", () => {
    self.skipWaiting();
});

self.addEventListener("activate", (event) => {
    event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", () => {
    // Intentionally empty — let the browser handle the request normally.
});
