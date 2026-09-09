# Plan

Umsetzung als eigenständiges Node.js-Backend (kein UI in diesem Schritt),
analog zum Aufbau von `../investment-analyzer/`.

1. **Datenmodell** (`src/db/schema.sql`, SQLite über `node:sqlite`): korrekte
   1:N- und M:N-Beziehungen gemäß der verbindlichen Regel in `README.md`,
   insbesondere die Join-Tabelle `appointment_proposal_orders`.
2. **Excel-Import** (Milestone 1) über `exceljs`: legt Hersteller, Geräte und
   je Gerät einen eigenen Wartungsauftrag mit fortlaufender Nummer
   (`WA-<Jahr>-<Nummer>`) an.
3. **Gruppierung nach Hersteller** (Milestone 2): offene Aufträge gruppieren,
   ausgewählte Aufträge zu einer gemeinsamen Wartungsanfrage bündeln
   (gemeinsame E-Mail, aber weiterhin getrennte Aufträge).
4. **Terminvorschlags-Erkennung** (Milestone 7/8): regelbasierter Parser für
   deutsche Datums-/Uhrzeitangaben, der Text anhand erkannter
   Inventarnummern in geräte-spezifische Abschnitte zerlegt (mehrere
   Geräte an einem Termin, unterschiedliche Termine pro Gerät, mehrere
   Alternativen pro Gerät - alle drei Fälle werden dadurch einheitlich
   behandelt).
5. **Termindauer-Fallback**: Herstellerangabe > gerätespezifische
   Standarddauer > Gerätetyp-Standarddauer > "Dauer unbekannt". Bei mehreren
   Geräten an einem Termin werden Einzeldauern aufsummiert.
6. **Outlook-Anbindung** (neuer Milestone): `CalendarClient`-Interface mit
   echter Graph-API-Implementierung und In-Memory-Mock; Verfügbarkeitsprüfung
   inkl. Arbeitszeit-Check, Zuordnung zu Terminstatus.
7. **Empfehlung** (Milestone 10): Greedy-Set-Cover über alle als FREI
   geprüften Terminvorschläge einer Gerätegruppe, um die Anzahl separater
   Servicetermine zu minimieren, mit Fälligkeits- und Kollisionskriterien als
   Tie-Breaker.
8. **Bestätigung/Verschiebung/Absage** (Milestone 11/12/15): Outlook-Termin
   wird erst nach Bestätigung angelegt; Verschiebung aktualisiert denselben
   Termin statt einen zweiten anzulegen; Absage markiert nur, löscht nie
   automatisch.
9. **Excel-Export** (Milestone 13) und **Dashboard-Kennzahlen** (Milestone 16,
   Basis): aggregierte Sicht auf Terminvorschläge/-status.
10. **Tests**: `node:test`, ein Testfall je Beispiel aus dem Lastenheft (siehe
    `tests/`).

## Bewusst nicht umgesetzt (siehe NEXT_STEPS.md)

Echte E-Mail-Anbindung (Milestone 3/4/6), KI-Auswertung abweichender
Formulierungen (Milestone 7 der ursprünglichen Zählung), Dashboard-/
Kalender-UI, Dokumentengenerierung, Erinnerungen, Produktivhärtung
(Logging/Backups/Audit-Trail) und Testmodus/Vollautomatisierung - diese
setzen auf der hier gebauten Datenschicht und Terminlogik auf, sind aber
eigene, deutlich größere Arbeitspakete.
