# TODO

- [x] Datenmodell mit korrekten 1:N-/M:N-Beziehungen (siehe README.md)
- [x] Excel-Import + Hersteller-Gruppierung (Milestone 1+2)
- [x] Terminvorschlags-Erkennung aus Freitext (Milestone 7/8, regelbasiert)
- [x] Termindauer-Fallback-Kette
- [x] Outlook-Kalenderanbindung (Graph-API + Mock) und Verfügbarkeitsprüfung
      (Milestone 9)
- [x] Empfehlungslogik mit Gerätebündelung (Milestone 10)
- [x] Bestätigen/Verschieben/Absagen inkl. Outlook-Synchronisation
      (Milestone 11/12/15)
- [x] Excel-Export erweitert (Milestone 13) + Dashboard-Kennzahlen
      (Milestone 16, Basis)
- [x] Automatisierte Tests für alle Lastenheft-Beispiele
- [ ] Echte E-Mail-Anbindung (Milestone 3/4/6) - Terminvorschlags-Erkennung
      erwartet aktuell rohen E-Mail-Text als Parameter statt ihn selbst
      abzurufen
- [ ] KI-Auswertung für Formulierungen, die der regelbasierte Parser nicht
      abdeckt (Milestone 7 der ursprünglichen Zählung)
- [ ] Automatische Erkennung von Absagen/Verschiebungen direkt aus
      E-Mail-Text (aktuell: Aufrufer identifiziert den betroffenen
      Terminvorschlag explizit)
- [ ] Dashboard-/Kalender-UI (aktuell nur Datenschicht)
- [ ] Dokumente/Wartungsberichte (Milestone 17)
- [ ] Logging, Backups, Audit-Trail (Milestone 18)
- [ ] Live-Test der echten Microsoft-Graph-Anbindung mit echten
      Azure-AD-Zugangsdaten (aktuell nur gegen den Mock getestet)
