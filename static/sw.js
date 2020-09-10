var STATUS = false;

if (STATUS) {
    var CACHE_STATIC_NAME = 'static';
    var CACHE_DYNAMIC_NAME = 'dynamic';

    var STATIC_FILES = [
        '/offline',
        '/app.js',
        '/fetch.js',
        '/promise.js',
        '/style.css',
        '/Farray.otf',
        '/HKGrotesk-Bold.otf',
        '/HKGrotesk-Light.otf',
        '/HKGrotesk-Medium.otf',
        '/HKGrotesk-Regular.otf',
        '/Modeka.otf',
        '/landing.jpg',
        '/favicon-16x16.png',
        '/favicon-32x32.png',
        '/favicon.ico',
        '/lab-offline.svg',
        '/ctftime-logo.png',
        '/facebook.png'
    ];

    self.addEventListener('install', function(event) {
        console.log('[WH] Installing Service Worker...', event);
        
        event.waitUntil(precache());
    });

    function precache() {
        console.log('[WH] Install Event processing');
        return caches.open(CACHE_STATIC_NAME)
            .then(function (cache) {
                console.log('[WH] Caching STATIC App Requests during Install');
                return cache.addAll(STATIC_FILES);
            })
    }

    self.addEventListener('activate', function(event) {
        console.log('[WH] Activating Service Worker...', event);
        event.waitUntil(
            caches.keys()
                .then(function (keyList) {
                    return Promise.all(keyList.map(function (key) {
                        if (key !== CACHE_STATIC_NAME && key !== CACHE_DYNAMIC_NAME) {
                            console.log('[WH] Removing old cache.', key);
                            return caches.delete(key);
                        }
                    }));
                })
        );
        return self.clients.claim();
    });

    self.addEventListener('fetch', function(event) {
        console.log('[WH] [FETCH] Serving requested asset: ' + event.request.url);
        event.respondWith(
            // currently serve from cache first, then network, then fallback to offline page for not available in cache
            // TODO: get data from both cache and network, if data from network is different than cache, then update cache otherwise don't update cache, finally return cache
            caches.match(event.request)
                .then(function (result) {
                    return result || fetch(event.request)
                        .then(function(response) {
                            return caches.open(CACHE_DYNAMIC_NAME)
                                .then(function(cache) {
                                    
                                    cache.put(event.request.url, response.clone());
                                    return response;
                                })
                        })
                        .catch(function(err) {
                            if (event.request.url === 'https://thewhitehat.club/status.svg') {
                                return caches.match('/lab-offline.svg');
                            } else {
                                return caches.match('/offline');
                            }
                        })
                })
        );
        
        // always remove status.svg from being cached
        caches.open(CACHE_DYNAMIC_NAME)
            .then(function(cache) {
                cache.match('https://thewhitehat.club/status.svg')
                    .then(function(result) {
                        if (result !== undefined) {
                            cache.delete('https://thewhitehat.club/status.svg')
                                .then(function(response) {
                                    if (response === true) {
                                        console.log('[WH] Removed status.svg from cache.');
                                    }
                            });
                        }
                    });
            });
    });
}
