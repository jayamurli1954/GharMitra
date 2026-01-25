const CACHE_NAME = 'gharmitra-v2';
const ASSETS_TO_CACHE = [
    '/manifest.json',
    '/icons/icon-192.png',
    '/icons/icon-512.png'
];

// Install Event - Skip waiting to activate immediately
self.addEventListener('install', (event) => {
    self.skipWaiting();
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('Static assets cached');
            return cache.addAll(ASSETS_TO_CACHE);
        })
    );
});

// Activate Event - Clear old caches and take control immediately
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
            );
        }).then(() => {
            return self.clients.claim();
        })
    );
});

// Fetch Event - Network first for HTML/JS, cache for static assets only
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Skip API calls - always live
    if (url.pathname.startsWith('/api/') || url.hostname !== self.location.hostname) {
        return;
    }

    // Network first for HTML and JS files (always get fresh)
    if (event.request.destination === 'document' ||
        url.pathname.endsWith('.html') ||
        url.pathname.endsWith('.js') ||
        url.pathname === '/') {
        event.respondWith(
            fetch(event.request).catch(() => caches.match(event.request))
        );
        return;
    }

    // Cache first for static assets (images, icons)
    event.respondWith(
        caches.match(event.request).then((response) => {
            return response || fetch(event.request);
        })
    );
});
