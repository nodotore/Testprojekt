"use strict";

/**
 * Service Worker für die gesamte Website inkl. der beiden PWAs
 * (Use-Case-Interview-App und CD Musikfinder). Cached das App-Shell,
 * damit die Seiten auf dem iPhone auch offline (bzw. bei instabiler
 * Verbindung) starten. Die eigentlichen Nutzdaten (Interview-Verlauf,
 * CD-Sammlung, Fotos) liegen in localStorage/IndexedDB, nicht im Cache.
 *
 * Für den CD Musikfinder werden zusätzlich alle sonstigen GET-Anfragen
 * (auch CDN-Ressourcen der optionalen Texterkennung) beim ersten
 * erfolgreichen Laden im Cache abgelegt, damit sie danach auch offline
 * funktionieren.
 */

var CACHE_NAME = "site-shell-v2";
var APP_SHELL = [
  "./index.html",
  "./leistungen.html",
  "./kontakt.html",
  "./use-case-app.html",
  "./cd-musikfinder.html",
  "./css/style.css",
  "./css/app.css",
  "./css/cd-musikfinder.css",
  "./js/script.js",
  "./js/use-case-app.js",
  "./js/cd-musikfinder.js",
  "./manifest.webmanifest",
  "./manifest-cd-musikfinder.webmanifest",
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

function isCacheableResponse(response) {
  if (!response) {
    return false;
  }
  // Opaque = No-CORS-Antwort von einer fremden Domain (z. B. CDN der
  // Texterkennung): Status ist immer 0/undurchsichtig, aber trotzdem
  // sinnvoll cachebar, damit sie offline erneut verwendet werden kann.
  if (response.type === "opaque") {
    return true;
  }
  return response.ok && (response.type === "basic" || response.type === "cors");
}

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
          if (isCacheableResponse(response)) {
            var responseClone = response.clone();
            caches.open(CACHE_NAME).then(function (cache) {
              cache.put(event.request, responseClone);
            });
          }
          return response;
        })
        .catch(function () {
          if (event.request.mode === "navigate") {
            return caches.match("./index.html");
          }
          return new Response("", { status: 504, statusText: "Offline" });
        });
    })
  );
});
