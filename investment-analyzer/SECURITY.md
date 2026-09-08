# Sicherheitsrichtlinie (Planungsstand Milestone 0)

**Status: geplant, wird ab Milestone 1 sukzessive umgesetzt und ab
Milestone 8 einem eigenen Security-Review unterzogen.** Verbindliche
Leitplanken gemäß Auftrag §12.

## Geltungsbereich Version 1

- Nur Research- und Simulationsmodus. **Keine Broker-Order-Funktion.**
  Kein Modul dieses Projekts darf in Version 1 in der Lage sein,
  tatsächliche Wertpapierorders auszulösen.
- Deutlicher, an jeder Berichtsausgabe sichtbarer Hinweis: allgemeine
  Information, keine individuelle Anlage-, Steuer- oder Rechtsberatung;
  Verluste bis zum Totalverlust sind möglich.

## Secrets

- Keine Zugangsdaten in Code, Logs, Git-Historie oder Exportdateien.
- Speicherung ausschließlich über System-Keyring (Windows Credential
  Manager) oder verschlüsselt (siehe `DECISIONS.md` ADR-5).
- `.gitignore` schließt lokale Secret-/Konfigurationsdateien aus, bevor
  Milestone 1 den ersten Commit mit echten Schlüsseln zulässt.
- Log-Ausgaben werden auf Secret-Muster geprüft (z. B. Redaction-Filter
  für bekannte API-Key-Formate), bevor sie persistiert werden.

## Umgang mit Webinhalten und Fremdtexten

- Inhalte von Webseiten, RSS-Feeds, PDFs und API-Antworten werden als
  **nicht vertrauenswürdig** behandelt.
- Prompt-Injection-Versuche in abgerufenen Texten (z. B. „ignoriere alle
  bisherigen Anweisungen") werden ignoriert; abgerufener Fremdtext wird
  dem Sprachmodell ausschließlich als zu verarbeitende Daten übergeben,
  nie als Instruktion.
- HTML wird vor jeder Weiterverarbeitung/Anzeige bereinigt (Sanitizing,
  kein `innerHTML` mit Rohinhalt, siehe bereits bestehende Konvention in
  diesem Repo unter `kontakt.html`).
- Downloadgrößen werden je Connector begrenzt (`ConnectorConfig.
  max_response_bytes`, Default 10 MB) — eine übergroße Antwort wird
  abgelehnt (`ConnectorValidationError`), bevor sie geparst oder gecacht
  wird; kein Retry, da eine Wiederholung dieselbe Größe liefert
  (`connectors/base.py::_request_with_retry`, Test in
  `tests/connectors/test_base_connector.py`).
- JSON-Antworten werden über `response.json()` geparst — ein
  strukturell ungültiges Ergebnis (auch absichtlich manipulierter
  Inhalt) führt zu einem `ConnectorValidationError` statt zu einer
  stillen Fehlinterpretation.

## SSRF-Schutz

- Jeder Connector erhält eine feste URL-Allowlist (Domain-Ebene); Abrufe
  außerhalb der Allowlist werden abgelehnt.
- Keine Anfragen an private/lokale Netzwerkbereiche (RFC 1918,
  Loopback, Link-Local) — DNS-Antworten werden vor dem Verbindungsaufbau
  geprüft, nicht nur die ursprüngliche Host-Angabe (Schutz gegen
  DNS-Rebinding).
- Umleitungen (HTTP-Redirects) werden grundsätzlich NICHT automatisch
  verfolgt (`httpx.Client` mit `follow_redirects=False`, dem Default —
  verifiziert im Security-Review Milestone 8). Das ist strenger als eine
  Allowlist-Prüfung pro Redirect-Sprung: eine 3xx-Antwort wird als
  gewöhnlicher (nicht per se fehlerhafter) Statuscode behandelt und ohne
  Folgeaufruf zurückgegeben, sodass ein Connector nie unbeabsichtigt
  einem Redirect außerhalb der Allowlist folgt.

## Rechtliche Nutzung von Quellen

- `robots.txt`, Nutzungsbedingungen, Urheberrecht, Rate Limits und
  Paywalls werden respektiert; keine Umgehung von Schutzmaßnahmen
  (Auftrag §3, §12). Playwright wird ausschließlich für rechtlich
  erlaubte Seiten ohne geeignete API eingesetzt, nie zur
  Paywall-/Bot-Schutz-Umgehung.
- Jede Quelle trägt einen Lizenzhinweis im Connector-Metadatum (siehe
  `DATA_SOURCES.md`); vor produktivem Einsatz einer neuen Quelle prüft
  der `data-source-agent` die aktuellen AGB.

## Audit-Log

- Vollständiges, append-only Audit-Log aller Datenabrufe (Quelle,
  Zeitpunkt, Ergebnis-Hash, Fehler) und aller generierten Berichte
  (welche Datenpunkte/Formeln eingeflossen sind).
- Audit-Log ist Teil der UI-Seite „Einstellungen, Quellen und
  Prüfprotokoll" (Auftrag §10, Seite 10).

## Abhängigkeiten und Software-Lieferkette

- `ruff`/`mypy` als Pflicht-Checks vor jedem Merge.
- Abhängigkeits-Scan (z. B. `pip-audit`) wird spätestens in Milestone 8
  in den Testlauf aufgenommen; bekannte kritische CVEs blockieren den
  Merge.
- Pinning der Abhängigkeitsversionen (Lockfile), keine ungeprüften
  „latest"-Installationen im Windows-Startskript.

## Fehlerverhalten bei Quellenausfall

- Fällt eine Quelle aus oder liefert unplausible/inkonsistente Daten,
  erscheint ein klarer, sichtbarer Fehler im UI/Report — niemals ein
  stillschweigend veralteter Wert, der als aktuell dargestellt wird
  (Auftrag §4, §15).

## Offene Punkte für Milestone 8 (Security-Review)

- Penetrationsartige Tests mit manipulierten/böswilligen Webinhalten
  (simulierte Prompt-Injection, überlange/fehlerhafte HTML-Antworten).
- Test mit absichtlich falschen/widersprüchlichen Testdaten (muss zu
  sichtbarer Warnung führen, nicht zu stiller Fehlkalkulation).
- Rate-Limit-Überschreitungstest je Connector.
- Restore-Prozess (Backup/Wiederherstellung der Datenbank) end-to-end
  getestet.
- Unabhängiger Security- und Plausibilitätscheck, dokumentiert
  (Auftrag §15).
