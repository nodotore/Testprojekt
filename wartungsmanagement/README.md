# Wartungsmanagement

Backend-Logik zur Verwaltung von Wartungsaufträgen für medizintechnische
Geräte: Hersteller können mehrere Geräte betreuen, mehrere Terminvorschläge
pro Gerät machen und mehrere Geräte an einem gemeinsamen Termin warten. Jeder
Terminvorschlag wird gegen einen Outlook-Kalender (Microsoft Graph API)
geprüft, bevor der Benutzer ihn bestätigt.

## Verbindliches Datenmodell

Diese Beziehung ist absichtlich **nicht** 1:1 und darf nirgends so
vereinfacht werden:

```
Ein Hersteller          → viele Geräte
Eine Wartungsanfrage     → mehrere Wartungsaufträge (= mehrere Geräte)
Ein Wartungsauftrag      → genau ein Gerät
Ein Gerät                → mehrere Terminvorschläge (über die Zeit)
Ein Terminvorschlag      → ein oder mehrere Wartungsaufträge/Geräte (M:N)
Ein bestätigter Termin   → mehrere Geräte möglich (folgt aus dem M:N)
Ein Outlook-Termin       → mehrere Wartungsaufträge möglich (folgt aus dem M:N)
```

Die M:N-Beziehung zwischen Terminvorschlag und Wartungsauftrag ist die
zentrale Tabelle `appointment_proposal_orders` (siehe `src/db/schema.sql`).
Ein Outlook-Kalendereintrag entspricht genau einem bestätigten
Terminvorschlag (`appointment_proposals.outlook_event_id`); da dieser bereits
mehrere Wartungsaufträge referenzieren kann, ist "ein Outlook-Termin → mehrere
Wartungsaufträge" damit ohne eigene Zusatztabelle erfüllt.

## Ausführen

```bash
npm install
npm test
```

Die Kernlogik läuft ohne externe Dienste (SQLite über das eingebaute
`node:sqlite`-Modul von Node 22, In-Memory- oder Datei-Datenbank). Für echte
Outlook-Prüfungen/-Termine werden Azure-AD-Zugangsdaten benötigt (siehe
unten) - ohne sie wird automatisch der In-Memory-Mock verwendet, mit dem sich
der komplette Ablauf lokal durchspielen lässt (siehe `tests/`).

## Module

| Modul | Zweck |
| --- | --- |
| `src/db/` | SQLite-Schema + Verbindung |
| `src/models/` | Datenzugriff (Hersteller, Geräte, Wartungsaufträge, -anfragen, Terminvorschläge) |
| `src/import/excelImport.js` | Milestone 1: Geräte-Import aus Excel |
| `src/grouping/groupByManufacturer.js` | Milestone 2: Gruppierung nach Hersteller, Bündelung zu Wartungsanfragen |
| `src/nlp/appointmentExtractor.js` | Milestone 7/8: Terminvorschläge aus E-Mail-Freitext erkennen (regelbasiert) |
| `src/duration/defaultDuration.js` | Termindauer-Fallback (Herstellerangabe → Gerät → Gerätetyp → unbekannt) |
| `src/outlook/` | Outlook-Kalenderanbindung: Interface, echte Graph-API-Implementierung, In-Memory-Mock, Verfügbarkeitsprüfung |
| `src/recommendation/recommend.js` | Milestone 10: Terminempfehlung inkl. Gerätebündelung |
| `src/workflow/` | Milestone 11/12/15: Bestätigen, Verschieben, Absagen |
| `src/export/excelExport.js` | Milestone 13: erweiterte Excel-Terminübersicht |
| `src/dashboard/dashboardSummary.js` | Milestone 16 (Basis): Kennzahlen + Kalenderansichten |

## Outlook / Microsoft Graph API

`src/outlook/calendarClient.js` wählt automatisch:

- **echte Anbindung** (`GraphCalendarClient`), wenn die Umgebungsvariablen
  `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` und
  `OUTLOOK_CALENDAR_USER` gesetzt sind. Benötigt eine Azure-AD-App-
  Registrierung mit der Anwendungsberechtigung `Calendars.ReadWrite`
  (Admin-Consent). Verwendet `/getSchedule` für die Verfügbarkeitsprüfung und
  `/events` zum Anlegen/Ändern von Terminen.
- **In-Memory-Mock** (`MockCalendarClient`) sonst - für lokale Entwicklung,
  Tests und Demos ohne Azure-AD-Zugang.

Outlook-Termine werden laut Workflow **erst nach Bestätigung durch den
Benutzer** angelegt (`workflow/confirmAppointment.js`), nie automatisch bei
der reinen Verfügbarkeitsprüfung. Eine Verschiebung aktualisiert immer den
bestehenden Termin (`outlook_event_id` bleibt erhalten); eine Absage markiert
den Termin nur (`[ABGESAGT]`-Präfix) und fragt den Benutzer, ob er wirklich
gelöscht werden soll - automatisches Löschen ist bewusst nicht implementiert.

## Umsetzungsstand

Siehe `PROGRESS.md` für den aktuellen Stand gegenüber der 20-Milestone-Liste
aus dem Lastenheft und `NEXT_STEPS.md` für offene Punkte (u. a. echte
E-Mail-Anbindung, KI-gestützte Auswertung abweichender Formulierungen,
Dashboard-/Kalender-UI, Dokumentengenerierung, Produktivhärtung).
