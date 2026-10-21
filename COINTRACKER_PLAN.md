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

## Offene Fragen
1. Steuerland und Regelwerk (Deutschland §23 EStG?) als Startpunkt?
2. Welche Börsen und Wallets sollen zuerst importiert werden?
3. Sollen Kursdaten live geladen werden oder reicht manuelle Eingabe für den Anfang?
