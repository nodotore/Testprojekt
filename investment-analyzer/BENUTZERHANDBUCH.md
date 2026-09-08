# Benutzerhandbuch — Investment-Analysator

Dieses Handbuch richtet sich an Endnutzer, die den Investment-Analysator
lokal unter Windows installieren und bedienen wollen. Es beschreibt den
tatsächlichen Stand des Programms ehrlich — auch dort, wo noch nicht
alles über die grafische Oberfläche bedienbar ist (siehe Abschnitt
„Was die Oberfläche heute zeigt — und was noch nicht"). Für technische
Hintergründe siehe `README.md`, `DECISIONS.md`, `METHODOLOGY.md`.

## Wichtiger Hinweis (bitte zuerst lesen)

Der Investment-Analysator liefert **allgemeine Information im
Research-/Simulationsmodus** — **keine individuelle Anlage-, Steuer-
oder Rechtsberatung** und **keine Kauf-/Verkaufsempfehlung**. Das
Programm handelt niemals automatisch Wertpapiere. Investitionen in
Wertpapiere können bis zum **Totalverlust** des eingesetzten Kapitals
führen. Jede Kennzahl, die das Programm zeigt, stammt entweder aus
einer konkreten, im Programm nachvollziehbaren Datenquelle oder ist als
Annahme/Schätzung ausdrücklich gekennzeichnet — es werden nie
Platzhalterzahlen angezeigt, die wie echte aktuelle Marktdaten aussehen.

## 1. Voraussetzungen

- Windows 10 oder 11.
- [Python 3.12 oder neuer](https://www.python.org/downloads/) — beim
  Installer unbedingt den Haken bei **„Add python.exe to PATH"**
  setzen, sonst findet `start.ps1` Python nicht.
- Internetzugang für den Datenabruf (SEC EDGAR, Alpha Vantage, GDELT,
  Investor-Relations-RSS-Feeds) — ohne Internetzugang lässt sich das
  Programm zwar starten, liefert aber keine Analysedaten.
- Optional, aber empfohlen für Kursdaten: ein kostenloser API-Schlüssel
  von [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
  (SEC EDGAR benötigt keinen Schlüssel, nur eine gültige
  Kontaktadresse im technischen User-Agent, die das Programm bereits
  automatisch setzt).

**Kein Doppelklick-Installer.** Es wird bewusst keine `.exe`-/`.msi`-
Installationsdatei mitgeliefert — die Entwicklungsumgebung, in der
dieses Projekt entstanden ist, hat keinen Zugriff auf
Windows-Build-Werkzeuge (Signierung, MSI-Paketierung), um ein solches
Paket zu erzeugen und ordnungsgemäß zu testen. Installation und Start
laufen stattdessen vollständig über die mitgelieferten Skripte
(`start.ps1`/`start.bat`) — siehe Abschnitt 2. Das ist eine bewusste,
dokumentierte Einschränkung, kein Versehen.

## 2. Installation und erster Start

1. Projektordner (`investment-analyzer/`) an einen beliebigen Ort auf
   dem Rechner kopieren bzw. das Repository dorthin auschecken.
2. Im Windows Explorer doppelt auf `start.bat` klicken.
   - Alternative über PowerShell:
     ```powershell
     cd Pfad\zu\investment-analyzer
     .\start.ps1
     ```
3. Beim ersten Start passiert automatisch, in dieser Reihenfolge:
   - Anlage einer eigenen, isolierten Python-Umgebung (`.venv`) —
     berührt keine sonstige Python-Installation auf dem Rechner.
   - Installation aller benötigten Programmbibliotheken.
   - Anlage/Aktualisierung der lokalen Datenbank (SQLite-Datei unter
     `%USERPROFILE%\InvestmentAnalyzer\investment_analyzer.db`) über
     Alembic-Migrationen. Ab dem zweiten Start wird die Datenbank vor
     jeder Migration automatisch gesichert (siehe Abschnitt 7).
   - Start der Streamlit-Oberfläche — öffnet sich automatisch im
     Standardbrowser, i. d. R. unter `http://localhost:8501`.
4. Beim allerersten Start erscheint die **Ersteinrichtung**: ein
   Analyseprofil (Märkte, Branchen, Ausschlüsse, Risikoklasse,
   Kandidatenzahl usw.) muss einmalig angelegt werden (Details siehe
   Abschnitt 4). Ohne akzeptierten Haftungsausschluss-Hinweis lässt
   sich das Profil nicht speichern.
5. Das Fenster/die Konsole, die sich beim Start öffnet, muss geöffnet
   bleiben, solange das Programm läuft. Schließen beendet die
   Anwendung. Ein erneuter Start läuft über denselben Doppelklick auf
   `start.bat`.

**Entwicklungsmodus:** `.\start.ps1 -Dev` installiert zusätzlich Test-/
Lint-Werkzeuge (nur für Entwickler relevant).

## 3. Wo werden meine Daten gespeichert?

Alles lokal auf diesem Rechner, standardmäßig unter
`%USERPROFILE%\InvestmentAnalyzer\`:

| Datei/Ordner | Inhalt |
| --- | --- |
| `investment_analyzer.db` | Die Datenbank (Analyseprofil-unabhängige Rohdaten: abgerufene Kennzahlen, Nachrichten, Watchlist/Portfolio, Prüfprotokoll). |
| `profile.json` | Das aktuelle Analyseprofil (Märkte, Ausschlüsse, Präferenzen). |
| `secrets.enc.json` | Verschlüsselt gespeicherte API-Schlüssel — nur als Fallback, falls der Windows Credential Manager (System-Keyring) nicht verfügbar ist. Siehe Abschnitt 6. |
| `logs/app.log` | Anwendungsprotokoll (Secrets werden vor dem Schreiben automatisch entfernt, siehe Abschnitt 6). |
| `backups/` | Datenbank-Sicherungen, siehe Abschnitt 7. |

Es werden keine Daten an einen eigenen Server dieses Projekts gesendet
— es gibt keinen. Netzwerkverbindungen gehen ausschließlich an die in
`DATA_SOURCES.md` gelistete Datenquellen (SEC EDGAR, Alpha Vantage,
GDELT, vom Nutzer angegebene Investor-Relations-Feeds), jeweils direkt
vom eigenen Rechner aus.

## 4. Das Analyseprofil (Ersteinrichtung)

Über „Profil bearbeiten" auf der Startseite jederzeit änderbar:

- **Märkte:** Anlageregionen (USA/Deutschland/übriges Europa/global),
  Börsen.
- **Branchen:** optionale Positiv-/Ausschlussliste.
- **Ausschlusswerte:** einzelne Ticker/ISIN, die nie berücksichtigt
  werden sollen.
- **Anlagepräferenzen:** Anlagehorizont, Risikoklasse, bevorzugter
  Stil, Referenzwährung, Vergleichsindex.
- **Marktkapitalisierung/Position/Kandidaten:** Mindest-/
  Höchstmarktkapitalisierung, maximale Positionsgröße (unverbindliche
  Bandbreite, keine Order-Vorgabe), gewünschte Kandidatenzahl.
- **Standard-Ausschlüsse:** Microcaps, Pennystocks, illiquide Werte
  wahlweise pauschal ausschließen.
- **Ausgabe:** Speicherort und Format (JSON/Excel/PDF) für Exporte.

Das Profil steuert, welche Datenpunkte/Berichte als „im Rahmen des
Auftrags" gelten — es ersetzt keine eigene Sorgfaltsprüfung.

## 5. Was die Oberfläche heute zeigt — und was noch nicht

**Bitte diesen Abschnitt aufmerksam lesen — er ist der wichtigste Teil
dieses Handbuchs für den aktuellen Stand.**

Die grafische Oberfläche zeigt aktuell genau eine Seite: **„Start /
Datenstatus"** — Ersteinrichtung/Profilverwaltung sowie eine ehrliche
Zählung dessen, was tatsächlich in der Datenbank steht (Anzahl
Unternehmen, Datenquellen, Datenpunkte). Solange noch kein Datenabruf
stattgefunden hat, zeigt diese Seite bewusst **Nullen** — niemals
Platzhalter- oder Beispielzahlen, die wie echte Marktdaten aussehen
könnten.

Die im Auftrag vorgesehenen weiteren neun Oberflächen-Seiten
(Marktscreener, Kandidaten-Rangliste, Unternehmensdetail,
Peer-Vergleich, DCF-/Szenarioanalyse, Nachrichten/Ereignisse,
Watchlist/Portfolio, Backtest, Einstellungen/Quellen/Prüfprotokoll)
sind **noch nicht als Bildschirmseiten gebaut** — sie werden bewusst
nicht als leere Platzhalter vorgezeigt, um keine Funktionalität
vorzutäuschen, die noch nicht existiert (Auftrag §16).

**Was bereits vollständig funktioniert und getestet ist** (nur noch
nicht über einen Button in der Oberfläche erreichbar): der komplette
Analysemotor — Datenabruf (SEC EDGAR, Alpha Vantage, GDELT, IR-RSS),
Kennzahlenberechnung, Bewertung (Multiples + DCF mit Szenarien),
erklärbares Scoring, Nachrichtenauswertung, Portfolio-/Watchlist-
Analyse, Backtesting sowie JSON-/Excel-/PDF-Export. Alle diese Bausteine
sind unabhängig voneinander getestet (445+ automatisierte Tests, siehe
`PROGRESS.md`) und lassen sich bereits heute über ein kurzes
Python-Skript aufrufen — das erfordert allerdings Grundkenntnisse in
Python. Ein vollständiges, tatsächlich lauffähiges Beispiel für den
gesamten Weg von der Datenbank bis zum fertigen Bericht (JSON/Excel/PDF)
findet sich in `tests/reports/test_bundle.py` und
`tests/reports/test_excel_export.py`/`test_pdf_export.py` — diese
Testdateien sind bewusst der verlässlichste Startpunkt für ein eigenes
Skript, da sie (anders als eine gesondert gepflegte Beispieldatei) bei
jeder Änderung automatisch mitgetestet werden und daher nie veralten.

Der Ausbau der restlichen Bildschirmseiten ist in `PLAN.md`/
`NEXT_STEPS.md` als nächster inhaltlicher Schritt nach Milestone 8
vorgesehen.

## 6. Datenschutz und Sicherheit

- **API-Schlüssel** (z. B. für Alpha Vantage) werden nie im Klartext
  in einer Datei oder im Programmcode gespeichert. Bevorzugt wird der
  Windows Credential Manager (System-Keyring) verwendet; steht dieser
  nicht zur Verfügung, greift ein verschlüsselter Datei-Fallback
  (`secrets.enc.json`, AES/Fernet-verschlüsselt mit einem aus einem
  Passwort abgeleiteten Schlüssel, siehe `DECISIONS.md` ADR-5).
- **Protokolle** (`logs/app.log`) werden vor dem Schreiben automatisch
  auf bekannte Geheimnis-Muster (API-Schlüssel, Tokens, Passwörter)
  geprüft und diese Stellen unkenntlich gemacht.
- **Netzwerksicherheit:** jeder Datenabruf ist auf eine feste Liste
  erlaubter Server-Adressen je Quelle beschränkt (keine Umleitung auf
  beliebige andere Adressen); Anfragen an private/interne
  Netzwerkbereiche werden technisch verhindert (Schutz vor
  sogenanntem SSRF/DNS-Rebinding). Downloadgrößen sind begrenzt, XML-
  Inhalte aus Investor-Relations-Feeds werden gegen böswillig
  konstruierte Dateien gehärtet geparst (siehe `SECURITY.md`,
  `DECISIONS.md` ADR-23/ADR-24 für Details des Sicherheits-Reviews).
- **Fremdinhalte** (Nachrichtentitel, RSS-Zusammenfassungen) stammen
  von externen, nicht vertrauenswürdigen Quellen und werden
  entsprechend behandelt: HTML/Skripte werden vor jeder Speicherung
  entfernt, der Text wird ausschließlich als Datum angezeigt, nie als
  Anweisung interpretiert.
- **Kein automatischer Handel:** Das Programm kann und wird nie
  eigenständig Wertpapierorders auslösen — es gibt keine
  Broker-Anbindung.

## 7. Datensicherung (Backup/Restore)

Die Datenbank ist eine einzelne Datei
(`%USERPROFILE%\InvestmentAnalyzer\investment_analyzer.db`). Zwei
Skripte sichern bzw. stellen sie wieder her:

```powershell
.\scripts\backup-database.ps1
```

Legt eine zeitgestempelte Kopie unter
`%USERPROFILE%\InvestmentAnalyzer\backups\` an. `start.ps1` ruft dies
automatisch vor jeder Datenbankmigration auf (überspringbar mit
`.\start.ps1 -NoBackup`); ein Fehlschlag (z. B. beim allerersten Start,
wenn noch keine Datenbank existiert) bricht den Programmstart NICHT ab,
sondern erscheint nur als Hinweis.

```powershell
.\scripts\restore-database.ps1
```

Ohne Angabe eines Pfads werden zunächst die vorhandenen Sicherungen
aufgelistet. Mit Pfad wird die aktuelle Datenbankdatei vollständig
durch den Inhalt der angegebenen Sicherung ersetzt:

```powershell
.\scripts\restore-database.ps1 "$env:USERPROFILE\InvestmentAnalyzer\backups\investment_analyzer-20260908T120000Z.db"
```

**Wichtig:** Der Investment-Analysator sollte während einer Sicherung
oder Wiederherstellung nicht laufen (geschlossenes Konsolenfenster),
damit die Datenbankdatei nicht gerade beschrieben wird. Nach einer
Wiederherstellung das Programm über `start.bat` neu starten.

## 8. Fehlerbehebung

**„Python 3.12 oder neuer wurde nicht gefunden"** — Python von
[python.org](https://www.python.org/downloads/) installieren, dabei
„Add python.exe to PATH" aktivieren, danach `start.bat` erneut starten.

**„Die Datenbank ist noch nicht migriert"** (Meldung in der
Oberfläche) — `start.ps1`/`start.bat` ausführen (nicht direkt
`streamlit run ...` aufrufen) — dieses Skript führt die nötige
Migration vor dem Start automatisch aus.

**Datenbankmigration schlägt fehl** — Konsolenausgabe genau lesen
(Alembic gibt den Grund aus). Vor einem erneuten Versuch die
automatisch erstellte Sicherung prüfen (Abschnitt 7); im Zweifel die
letzte funktionierende Sicherung wiederherstellen.

**Port 8501 bereits belegt** — ein anderes Programm (evtl. eine
vorherige, nicht sauber beendete Instanz) belegt den Port. Alle
Streamlit-/Python-Fenster schließen und erneut starten, oder
Task-Manager prüfen.

**Datenabruf schlägt fehl / Fehlermeldung statt Zahlen** — das ist
gewolltes Verhalten (Auftrag §4: „Fail loud, nicht silent"): fällt eine
Datenquelle aus oder liefert unplausible Daten, erscheint ein klarer
Fehler statt eines stillschweigend veralteten oder erfundenen Werts.
Häufigste Ursachen: kein Internetzugang, fehlender/ungültiger
Alpha-Vantage-API-Schlüssel, Rate-Limit der jeweiligen Quelle
überschritten (kurz warten und erneut versuchen).

**Weitere Probleme** — Konsolenausgabe und `logs/app.log` prüfen
(Geheimnisse sind dort bereits automatisch entfernt, die Meldung selbst
ist unverändert lesbar).

## 9. Tests ausführen (nur für technisch interessierte Nutzer)

```powershell
.\scripts\run-tests.ps1
```

Führt Codeprüfung (`ruff`), Typprüfung (`mypy`) und die vollständige
automatisierte Testsuite aus. Nicht für den normalen Betrieb nötig,
aber der zuverlässigste Weg, den aktuellen, tatsächlich funktionierenden
Funktionsumfang nachzuvollziehen (siehe Abschnitt 5).

## 10. Weiterführende Dokumente

| Dokument | Inhalt |
| --- | --- |
| `AUFTRAG.md` | Der vollständige, unveränderte Originalauftrag. |
| `METHODOLOGY.md` | Wie Kennzahlen, Bewertung und Score berechnet werden. |
| `DATA_SOURCES.md` | Welche Datenquelle für was verwendet wird, Lizenzhinweise. |
| `SECURITY.md` | Sicherheitsrichtlinie und Ergebnisse des Milestone-8-Reviews. |
| `PROGRESS.md` | Was ist fertig, was noch offen. |
| `DECISIONS.md` | Alle Architektur-/Sicherheitsentscheidungen (ADR-1 bis ADR-24). |
