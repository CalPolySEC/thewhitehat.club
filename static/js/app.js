if (!window.Promise) {
    window.Promise = Promise;
}

if ('serviceWorker' in navigator) {
    navigator.serviceWorker
        .register('/sw.js', {
            scope: '/'
        })
        .then(function(reg) {
            console.log('[WH] Service Worker registered! Scope is: ' + reg.scope);
            if (!navigator.serviceWorker.controller) {
                return
            }
        })
        .catch(function(err) {
            console.log('[WH] Service Worker registration failed with error: ' + err);
        });

    if (navigator.serviceWorker &&
        navigator.serviceWorker.getRegistration) {
            navigator.serviceWorker.getRegistration().then(reg => {
                reg.onupdatefound = function() {
                    const installingWorker = reg.installing;
                    installingWorker.onstatechange = function() {
                        if (installingWorker.state === 'activated') {
                            // auto-reload the page after service worker installs and finishes activating, in order to start caching
                            console.log('[WH] RELOADING!');
                            window.location.reload();
                        }
                    };
                };
            });
        }
}