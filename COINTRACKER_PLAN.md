# Krypto-Tracker (CoinTracking-Alternative) – Plan

Status: Entwurf zur Prüfung. Es wurde noch kein Code geschrieben.

## Ziel
Eine eigene, lokale Krypto-Portfolio- und Steuer-App im Stil von CoinTracking.
Statische PWA (HTML/CSS/JS), alle Daten bleiben im Browser (IndexedDB). Kein Server, keine Konten.

## Abgrenzung
- Funktionen werden aus dem öffentlich bekannten Funktionsumfang abgeleitet.
- Kein Code, keine Texte, kein Branding und keine Assets von CoinTracking werden übernommen.
- REA (Reverse Engineer Anything) ist optional und nur für die Beobachtung der öffentlichen Website
  (Seitenstruktur, Netzwerkaufrufe) vorgesehen. Es ist derzeit nicht installiert (Berechtigung ausstehend).

## Funktionsumfang (MVP → später)
| Phase | Funktion |
|-------|----------|
| 1 | Transaktions-Ledger: Kauf, Verkauf, Tausch, Transfer, Gebühr, Einnahme (Staking/Airdrop) |
| 1 | CSV-Import (generisches Format + Vorlagen für 2–3 Börsen), Dubletten-Erkennung |
| 1 | Manuelle Eingabe und Bearbeitung von Transaktionen |
| 2 | Portfolio-Bestand je Coin/Wallet/Börse, Kosten-Basis, unrealisierter Gewinn |
| 2 | Kursdaten (öffentliche API, z. B. CoinGecko), Cache und Offline-Fallback |
| 3 | Realisierte Gewinne: FIFO (später LIFO/HIFO), Haltefrist-Kennzeichnung (1 Jahr, DE) |
| 3 | Berichte: Jahresübersicht, Gewinn/Verlust, Export als CSV/PDF |
| 4 | Dashboard-Diagramme (Wert über Zeit, Verteilung) |
| 4 | Backup/Restore (JSON), PWA-Installation, Offline-Betrieb |

## Architektur
- `cointracker/index.html` – Einstiegsseite, Navigation
- `cointracker/js/db.js` – IndexedDB-Zugriff
- `cointracker/js/ledger.js` – Transaktionsmodell und Validierung
- `cointracker/js/import/` – CSV-Parser je Börse
- `cointracker/js/prices.js` – Kursabruf und Cache
- `cointracker/js/tax.js` – FIFO-Lots, realisierte Gewinne
- `cointracker/js/reports.js` – Berichte und Export
- `cointracker/tests/` – Tests für Import und Steuerlogik (Node-Testrunner)
- Service Worker und Manifest nach dem Muster der bestehenden Apps im Repo.

## Datenmodell (Transaktion)
`id, datum, typ, menge_ein, währung_ein, menge_aus, währung_aus, gebühr, gebühr_währung, ort, notiz, quelle_hash`

## Risiken
- Steuerregeln sind länderspezifisch und ändern sich. Die App gibt keine Steuerberatung (Hinweis in der UI).
- Börsen-CSV-Formate ändern sich. Parser brauchen Beispieldateien zum Testen.
- Kurs-APIs haben Ratenlimits. Cache und Fallback sind nötig.

## Entscheidungen
- Steuerland: Deutschland (§23 EStG, Haltefrist 1 Jahr, Freigrenze 600 € bis 2023 / 1.000 € ab 2024; §22 Nr. 3 Freigrenze 256 €).
- Quellen: Ledger (Ledger Live CSV) und 21bitcoin.
- Kurse: vorerst manueller EUR-Wert je Transaktion (Live-Kurse später).
- Speicher: localStorage statt IndexedDB für den MVP.

## Stand
- Umgesetzt (`cointracker/`): Ledger, generischer CSV-Import, Ledger-Live-Import, FIFO mit Haltefrist, Jahresbericht, Backup, 11 Tests (`node --test tests/tax.test.mjs`).
- Offen: 21bitcoin-Import (Beispiel-Export nötig, Format wird nicht geraten), Wallet-genaue FIFO, Live-Kurse, Diagramme, PWA/Offline.
- Ledger-Live-Import: IN/OUT werden als Übertragungen importiert. Zahlungen an Dritte müssen manuell als Verkauf erfasst werden.
