const CACHE_NAME = 'banca-v1';
const URLs_TO_CACHE = [
    './',
    './index.html',
    './manifest.json'
];

// Instalação: cache das URLs estáticas
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(URLs_TO_CACHE))
            .then(() => self.skipWaiting())
    );
});

// Ativação: limpar cache antigo
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys => {
            return Promise.all(
                keys.filter(key => key !== CACHE_NAME)
                    .map(key => caches.delete(key))
            );
        })
    );
});

// Fetch: tentar rede primeiro, fallback para cache
self.addEventListener('fetch', event => {
    event.respondWith(
        fetch(event.request)
            .catch(() => caches.match(event.request))
    );
});
