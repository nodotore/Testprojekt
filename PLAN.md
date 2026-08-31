# Plan

## UC-001 – CD Musikfinder

Umsetzung als PWA (Begründung: siehe `DECISIONS.md`).

1. **Datenmodell (IndexedDB, `cdMusikfinderDB`)**
   - Store `cds`: `{ id, interpret, album, songs[], ordner, ocrText, photo (Blob), createdAt, updatedAt }`
   - Store `undo`: automatische Sicherungen (autoIncrement), `{ type, label, snapshot, createdAt }`
   - Store `draft`: einzelner Datensatz für einen laufenden, unterbrechbaren Erfassungsvorgang
2. **Bildschirme** (`cd-musikfinder.html`, ein Screen jeweils sichtbar): Bibliothek/Suche,
   Foto-Aufnahme mit Qualitätsprüfung, Verarbeitung (OCR-Fortschritt), Angaben
   erfassen/bearbeiten, Detailansicht, Backup & Regale.
3. **Bildqualitätsprüfung** vor der Bestätigung: Helligkeit + Unschärfe
   (Varianz des Laplace-Werts) über ein herunterskaliertes Graustufenbild,
   rein clientseitig per Canvas.
4. **OCR**: Tesseract.js bei Bedarf nachladen, mit Timeout und Fallback auf
   manuelle Eingabe.
5. **Sortierung & Fundort-Vorschlag**: alphabetisch nach Regal, Interpret,
   Album; Positions- und Nachbarschafts-Berechnung für den Vorschlagstext.
6. **Suche**: über Interpret, Album und Songtitel, mit Trefferanzeige.
7. **Rückgängig/Backup**: Snapshot vor jeder zerstörenden Änderung,
   Ein-Klick-Rückgängig auf dem Startbildschirm, browsbare Liste, manueller
   JSON-Export.
8. **Wiederaufnahme**: laufender Erfassungsvorgang wird als Entwurf
   gespeichert und beim nächsten Start zum Fortsetzen angeboten.
9. **Offlinefähigkeit**: `sw.js` erweitert (App-Shell aller Seiten +
   generisches Runtime-Caching), eigenes Manifest
   `manifest-cd-musikfinder.webmanifest`.
10. **Einbindung**: Navigationslink auf allen bestehenden Seiten
    (`index.html`, `leistungen.html`, `kontakt.html`).

## Test-Strategie

Da in dieser Umgebung kein Xcode/echtes iPhone zur Verfügung steht, wurde
die PWA mit Playwright/Chromium (headless) End-to-End getestet: Erfassen
(Kamera-Datei-Input + manuell), Sortierung, Suche (Treffer/kein Treffer),
Bildqualitätsprüfung (synthetisch scharfes vs. dunkles/kontrastarmes
Testbild), Löschen + Rückgängig, Backup-Export, Offline-Verhalten
(Service Worker + IndexedDB nach `context.setOffline(true)`), sowie
Wiederaufnahme eines unterbrochenen Vorgangs nach Neuladen der Seite.
Ein manueller Test auf einem echten iPhone (Kamera-Zugriff, Safari-
Installation "Zum Home-Bildschirm", echte Fotos) steht noch aus.
