# Fortschritt

Stand gegenüber der 20-Milestone-Liste aus dem Lastenheft
("Erweiterung: mehrere Geräte, mehrere Termine und Outlook-Kalenderabgleich"):

| Milestone | Status |
| --- | --- |
| 1. Excel-Import und Datenbank | ✅ Umgesetzt (`src/import/excelImport.js`) |
| 2. Hersteller und mehrere Geräte gruppieren | ✅ Umgesetzt (`src/grouping/groupByManufacturer.js`) |
| 3. E-Mail-Vorlagen | ⏭️ Nicht umgesetzt |
| 4. E-Mail-Anbindung | ⏭️ Nicht umgesetzt |
| 5. Wartungsstatus und Historie | 🟡 Teilweise (Auftragsstatus vorhanden, keine Historie/Log) |
| 6. Eingehende Antworten erkennen | ⏭️ Nicht umgesetzt (E-Mail-Text wird als Parameter erwartet) |
| 7. KI-Auswertung der E-Mails | 🟡 Regelbasierter Ersatz statt echter KI (`src/nlp/appointmentExtractor.js`) |
| 8. Mehrere Terminvorschläge erkennen und speichern | ✅ Umgesetzt, inkl. Mehrgeräte-/Mehrtermin-Fälle |
| 9. Outlook-Kalender lesen und Verfügbarkeit prüfen | ✅ Umgesetzt (`src/outlook/`) |
| 10. Terminvergleich und intelligente Empfehlungen | ✅ Umgesetzt (`src/recommendation/recommend.js`) |
| 11. Termin durch Benutzer bestätigen | ✅ Umgesetzt (`src/workflow/confirmAppointment.js`) |
| 12. Outlook-Kalendereintrag erstellen und synchronisieren | ✅ Umgesetzt |
| 13. Excel-Wartungskalender erzeugen | ✅ Umgesetzt (`src/export/excelExport.js`) |
| 14. Erinnerungen und unbeantwortete Anfragen | ⏭️ Nicht umgesetzt |
| 15. Absagen und Terminverschiebungen erkennen | 🟡 Verarbeitung umgesetzt (`src/workflow/`); automatische Erkennung aus E-Mail-Text noch nicht |
| 16. Dashboard | 🟡 Kennzahlen/Kalenderabfragen als Datenschicht vorhanden (`src/dashboard/`), keine UI |
| 17. Dokumente und Wartungsberichte | ⏭️ Nicht umgesetzt |
| 18. Logging, Backups und Audit-Trail | ⏭️ Nicht umgesetzt |
| 19. Testmodus | 🟡 `node:test`-Suite vorhanden; kein separater Anwendungs-Testmodus |
| 20. Produktivmodus und Vollautomatisierung | ⏭️ Nicht umgesetzt |

## Datenmodell und Kernregeln

Die verbindliche Beziehungsregel (Hersteller 1:N Geräte, Wartungsanfrage 1:N
Wartungsaufträge, Terminvorschlag M:N Wartungsauftrag, ...) ist vollständig
im Schema abgebildet und automatisiert getestet (`tests/`), inkl. aller im
Lastenheft konkret vorgerechneten Beispiele:

- Fresenius-Beispiel (3 Geräte, gemeinsame Anfrage, getrennte Aufträge
  `WA-2026-00101/00102/00103`)
- "15.09., 18.09. oder 22.09.2026" → drei Terminvorschläge
- mit Uhrzeiten ("15.09.2026 – 08:00 Uhr", ...)
- "alle fünf Geräte" an einem Termin → ein Terminvorschlag, fünf verknüpfte
  Aufträge
- unterschiedliche Termine pro Gerät (MT-1001/1002/1003)
- mehrere Alternativen pro Gerät
- Outlook-Beispiel (15.09. belegt, 16.09./18.09. frei → empfohlen)
- Termindauer-Tabelle (Dialysegerät 2h, Patientenmonitor 1h, Defibrillator
  1,5h) inkl. "Dauer unbekannt"-Fall
- Montag/Dienstag/Donnerstag-Empfehlungsbeispiel (Donnerstag bevorzugt, da
  alle drei Geräte gemeinsam möglich)
- Bestätigung → Outlook-Termin mit Titel/Beschreibung wie im Beispiel
- Verschiebung ändert denselben Outlook-Termin
- Absage markiert, löscht nicht automatisch

Alle 25 automatisierten Tests sind grün (`npm test`).
