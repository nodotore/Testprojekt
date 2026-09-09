# Nächste Schritte

1. Mit dem Benutzer klären, welches Postfach/welcher Kalender als
   `OUTLOOK_CALENDAR_USER` dienen soll, und eine Azure-AD-App-Registrierung
   mit der Anwendungsberechtigung `Calendars.ReadWrite` anlegen (Admin-
   Consent), um `GraphCalendarClient` live zu testen.
2. Milestone 3/4/6 (E-Mail-Vorlagen, echte E-Mail-Anbindung, Erkennung
   eingehender Antworten) umsetzen, damit `appointmentExtractor.js` nicht
   mehr manuell mit E-Mail-Text aufgerufen werden muss.
3. Entscheiden, ob/wann eine echte KI-Auswertung (LLM) die regelbasierte
   Terminerkennung ergänzt oder ablöst, für Formulierungen außerhalb der im
   Lastenheft vorgegebenen Muster.
4. Dashboard-/Kalender-UI auf Basis von `src/dashboard/dashboardSummary.js`
   bauen (Ansichten Heute/Woche/Monat/Hersteller/Gerät/Standort inkl.
   farblicher Kennzeichnung, wie im Lastenheft als "später" vorgesehen).
5. Milestone 14/17/18/19/20 (Erinnerungen, Dokumente/Berichte,
   Logging/Backups/Audit-Trail, Testmodus, Produktivhärtung) angehen, sobald
   die Kernlogik im echten Betrieb erprobt ist.
