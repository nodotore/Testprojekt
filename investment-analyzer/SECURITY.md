# Sicherheitsrichtlinie (Stand Milestone 8, Security-Review abgeschlossen)

**Status: umgesetzt.** Verbindliche Leitplanken gemäß Auftrag §12,
seit Milestone 1 sukzessive implementiert und in Milestone 8 durch
einen zweistufigen Security-Review geprüft — zunächst ein eigener
Review (`DECISIONS.md` ADR-23/ADR-24), anschließend ein unabhängiger,
separater Review-Durchlauf (ADR-25), der einen echten, in Auftrag §15
relevanten Look-ahead-Bias fand (seither behoben) sowie zwei weitere
Härtungen anstieß. Dieses Dokument beschreibt den TATSÄCHLICHEN Stand,
nicht mehr nur die Planung — jede Behauptung hier wurde gegen den
Code verifiziert.

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
  max_response_bytes`, Default 10 MB) — die Antwort wird gestreamt
  gelesen und der Download WÄHREND des Empfangs abgebrochen, sobald die
  Grenze überschritten wird (`ConnectorValidationError`, kein Retry, da
  eine Wiederholung dieselbe Größe liefert; kein Cache-Eintrag für eine
  abgebrochene Antwort). Ursprünglich wurde die Antwort erst vollständig
  gepuffert und danach geprüft — das begrenzte die Verarbeitung, aber
  nicht den Speicherverbrauch während des Downloads selbst; auf Befund
  des unabhängigen Reviews (ADR-25) auf echtes Streaming umgestellt
  (`connectors/base.py::_request_with_retry`, Tests in
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
- **Bekannte, bewusst nicht behobene Restlücke (ADR-25):** Die DNS-
  Prüfung (`connectors/ssrf.py::assert_safe_url`) löst den Hostnamen
  selbst auf und validiert die IP — die anschließende tatsächliche
  HTTP-Anfrage (`httpx.Client`) führt danach ihre EIGENE, erneute
  DNS-Auflösung durch. Zwischen Prüfung und Verbindungsaufbau liegt ein
  theoretisches Zeitfenster (u. a. Rate-Limiter-Wartezeit,
  Retry-Backoff), in dem sich der DNS-Eintrag ändern könnte
  (Time-of-check-to-time-of-use). Ein Angreifer bräuchte dafür Kontrolle
  über die DNS-Auflösung eines bereits erlaubten Hosts — am ehesten
  relevant bei `ir_rss.py`, dessen Host je Emittent variiert. Für dieses
  lokale Ein-Nutzer-Werkzeug (kein Mehrbenutzer-/Internet-Dienst)
  bewusst als tragbares Restrisiko eingestuft statt eines riskanten,
  kurzfristigen Umbaus der HTTP-Transportschicht (IP-Pinning würde eine
  eigene `httpx`-Transport-Implementierung erfordern). Empfohlene
  künftige Behebung: validierte IP über einen eigenen Transport/Resolver
  fest an die tatsächliche Verbindung binden, dokumentiert in
  `NEXT_STEPS.md`.
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

- `ruff`/`mypy` als Pflicht-Checks vor jedem Merge (durchgängig grün
  gehalten, 453 Tests, Stand 2026-09-08).
- Abhängigkeits-Scan per `pip-audit` in Milestone 8 durchgeführt:
  „No known vulnerabilities found" (Stand 2026-09-08, siehe ADR-23).
  Noch NICHT automatisiert in den regulären Testlauf integriert (kein
  CI-System in diesem Projekt) — bei jedem künftigen Abhängigkeits-
  Update manuell erneut auszuführen.
- **Offen:** Pinning der Abhängigkeitsversionen über ein echtes
  Lockfile (z. B. `pip-compile`/`uv lock`) ist NICHT umgesetzt —
  `pyproject.toml` verwendet ausschließlich `>=`-Untergrenzen, `start.
  ps1` installiert ohne Lockfile. Als offener Punkt dokumentiert statt
  stillschweigend als erledigt behandelt (siehe `NEXT_STEPS.md`).

## Fehlerverhalten bei Quellenausfall

- Fällt eine Quelle aus oder liefert unplausible/inkonsistente Daten,
  erscheint ein klarer, sichtbarer Fehler im UI/Report — niemals ein
  stillschweigend veralteter Wert, der als aktuell dargestellt wird
  (Auftrag §4, §15).

## Milestone-8-Security-Review — Abschluss

Alle ursprünglich hier gelisteten Prüfpunkte wurden durchgeführt; siehe
`DECISIONS.md` ADR-23 (eigener Review: Downloadgrößen-Begrenzung,
Log-Redaction, Pflichthinweis in Exporten, Redirect-Dokumentation),
ADR-24 (Ausfalltests: XML-Entity-Expansion im IR-RSS-Connector
gefunden und behoben, Prompt-Injection- und Widerspruchsdaten-
Ausfalltests, Restore-Prozess neu gebaut und getestet) und ADR-25
(unabhängiger, separater Review-Durchlauf: ein echter Look-ahead-Bias
in den Warnsignal-Checks gefunden und behoben, Downloadgrößen-Prüfung
auf echtes Streaming umgestellt, HTML-Sanitizing-Fallback gehärtet,
SSRF-Restlücke ehrlich dokumentiert statt verschwiegen).

**Verbleibende, bewusst offene Punkte** (siehe `NEXT_STEPS.md` für
Details): Lockfile für Abhängigkeits-Pinning, SSRF-IP-Pinning bis zur
tatsächlichen Verbindung (siehe Abschnitt „SSRF-Schutz" oben),
Auftrag-§3-„bei Widerspruch beide Werte zeigen" (mit dem aktuellen
Kostenlos-Quellen-Set strukturell nicht auftretbar, siehe ADR-24).
Ehrliche Gesamtbewertung gegen alle neun Auftrag-§15-Abnahmekriterien:
`ABNAHME.md`.
