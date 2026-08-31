# Fortschritt

## UC-001 – CD Musikfinder

**Status: MVP implementiert und automatisiert getestet.**

Umgesetzt:
- Foto-Erfassung mit Bildqualitätsprüfung und Bestätigung
- Optionale Texterkennung (Tesseract.js) mit Fallback auf manuelle Eingabe
- Manuelle Erfassung/Bearbeitung von Interpret, Album, Songtiteln, Regal
- Automatische Sortierung + Fundort-Vorschlag
- Suche über Interpret/Songtitel
- Rückgängig-Funktion + automatische Sicherung vor Löschen/Bearbeiten
- Manueller JSON-Export der gesamten Sammlung
- Wiederaufnahme eines unterbrochenen Erfassungsvorgangs
- Offlinefähigkeit über Service Worker (App-Shell + Runtime-Cache) und
  IndexedDB
- Navigationseinbindung in die bestehende Website

Getestet (Playwright/Chromium, siehe `PLAN.md` → Test-Strategie): alle
Kernabläufe inkl. Fehlerfälle (schlechte Bildqualität, keine Daten
vorhanden, kein Suchtreffer) laufen wie erwartet; keine
JavaScript-Fehler außer dem erwarteten Netzwerkfehler beim
CDN-Nachladen der Texterkennung in dieser Sandbox-Umgebung (dort ist
ausgehender Zugriff auf `cdn.jsdelivr.net` durch die Netzwerk-Policy
gesperrt - der dafür vorgesehene Fallback greift korrekt).

Noch offen: echter Test auf einem iPhone (Kamera, Safari-Installation),
Klärung der in `USE_CASES.md` unter UC-001 → "Offene Punkte" gelisteten
Fragen.
