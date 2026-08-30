"use strict";

/**
 * Service Worker für die Use-Case-Interview-App.
 * Cached das App-Shell, damit die Seite auf dem iPhone auch offline
 * (bzw. bei instabiler Verbindung) startet. Interview-Antworten selbst
 * liegen in localStorage, nicht im Cache.
 */

var CACHE_NAME = "use-case-app-v1";
var APP_SHELL = [
  "./use-case-app.html",
  "./css/style.css",
  "./css/app.css",
  "./js/use-case-app.js",
  "./manifest.webmanifest",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
];

self.addEventListener("install", function (event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function (cache) {
      return cache.addAll(APP_SHELL);
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys
          .filter(function (key) {
            return key !== CACHE_NAME;
          })
          .map(function (key) {
            return caches.delete(key);
          })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener("fetch", function (event) {
  if (event.request.method !== "GET") {
    return;
  }

  event.respondWith(
    caches.match(event.request).then(function (cached) {
      if (cached) {
        return cached;
      }
      return fetch(event.request)
        .then(function (response) {
          if (response && response.ok && response.type === "basic") {
            var responseClone = response.clone();
            caches.open(CACHE_NAME).then(function (cache) {
              cache.put(event.request, responseClone);
            });
          }
          return response;
        })
        .catch(function () {
          return caches.match("./use-case-app.html");
        });
    })
  );
});
