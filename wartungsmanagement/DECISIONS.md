# Entscheidungen

## Kein bestehendes Projekt als Basis

Im Repository existierte vor dieser Umsetzung kein Wartungsmanagement-System
- das Lastenheft beschreibt eine "Erweiterung" von Milestones 1-7 eines
Grundsystems, das es hier nicht gab. Auf Rückfrage wurde entschieden, direkt
ein neues, vollständiges Grundgerüst samt der beschriebenen Erweiterungen zu
bauen (kein separates Use-Case-Interview vorab), als eigener Ordner analog zu
`../investment-analyzer/`.

## Node.js-Backend statt Fortführung des statischen Website-Stacks

Das restliche Repository ist eine statische Website ohne Backend. Outlook/
Microsoft-Graph-Integration, eine relationale Datenbank mit mehreren
verknüpften Tabellen und serverseitige Terminlogik benötigen zwingend ein
Backend - eine reine Client-PWA (wie beim CD-Musikfinder) wäre hier nicht
sinnvoll, u. a. weil Azure-AD-Client-Secrets niemals im Browser landen
dürfen.

## SQLite über `node:sqlite` statt `better-sqlite3`/ORM

Node 22 bringt mit `node:sqlite` eine synchrone SQLite-Anbindung ohne native
Kompilierung mit. Das vermeidet Build-Probleme in Sandbox-/CI-Umgebungen
(kein `node-gyp`) und ist für den hier benötigten Umfang (wenige Tabellen,
klare Beziehungen) ausreichend. Migrationswerkzeug/ORM wäre für den
aktuellen Umfang verfrühte Abstraktion.

## `exceljs` statt `xlsx` (SheetJS)

`xlsx` hat zwei unbehobene hochkritische Sicherheitslücken (Prototype
Pollution, ReDoS) ohne verfügbaren Fix. Da hiermit potenziell extern
zugelieferte Excel-Dateien (Herstellerlisten) geparst werden, wurde
stattdessen `exceljs` verwendet. `exceljs` selbst zieht aktuell eine
`uuid`-Version mit einer bekannten, aber nur bei explizit übergebenem Buffer
relevanten Schwachstelle (moderate Einstufung) nach - hier nicht ausnutzbar,
da kein eigener Buffer an `uuid` übergeben wird.

## M:N-Terminvorschlag statt 1:N wie im Beispiel-Tabellenschema

Das Lastenheft schlägt für `appointment_proposals` beispielhaft eine Spalte
"Wartungsauftrag-ID" vor. Die zuvor im selben Dokument als "besonders
wichtige Regel" festgelegte Beziehung ("Ein Terminvorschlag → ein oder
mehrere Wartungsaufträge") ist damit aber nicht abbildbar. Umgesetzt wurde
stattdessen eine Join-Tabelle `appointment_proposal_orders` - das
Beispielschema war als Illustration zu verstehen, die ausdrücklich
formulierte Kardinalitätsregel hat Vorrang.

## Kein eigener `outlook_events`-Table

Da ein Outlook-Termin laut Regel "mehrere Wartungsaufträge" betreffen kann
und ein bestätigter Terminvorschlag bereits M:N mit Wartungsaufträgen
verknüpft ist, würde eine zusätzliche `outlook_events`-Tabelle mit eigener
Join-Tabelle dieselbe Information redundant zweimal abbilden. Stattdessen
trägt `appointment_proposals` direkt `outlook_event_id`/`_start`/`_end`.

## Terminvorschlags-Erkennung: regelbasiert statt LLM/KI

Das Lastenheft sieht für Freitext-E-Mails perspektivisch eine "KI-Auswertung"
vor (eigener, späterer Milestone). Für die in diesem Schritt konkret
vorgegebenen Beispielformulierungen wurde ein deterministischer,
regelbasierter Parser gebaut (`src/nlp/appointmentExtractor.js`). Vorteil:
reproduzierbar, ohne externe API-Abhängigkeit, vollständig testbar. Für
abweichende, nicht vorhersehbare Formulierungen ist er nicht robust - das ist
bewusst so und für den späteren KI-Milestone vorgesehen, der auf denselben
strukturierten Datentypen aufsetzen kann.

## Dauer bei mehreren Geräten an einem Termin: Summe statt Maximum

Das Lastenheft macht dazu keine explizite Vorgabe. Da ein Techniker mehrere
Geräte bei einem Vor-Ort-Termin nacheinander wartet, wurde die Gesamtdauer
als Summe der (Standard-)Einzeldauern aller beteiligten Geräte berechnet,
nicht als Maximum. Nennt der Hersteller selbst eine Gesamtdauer im Text, hat
diese immer Vorrang vor der berechneten Summe.

## Outlook-Anbindung: Graph-Client mit austauschbarem Mock

Da in dieser Umgebung keine Azure-AD-Zugangsdaten vorliegen, wurde die echte
Graph-API-Anbindung (`GraphCalendarClient`, Client-Credentials-Flow über
`/getSchedule` und `/events`) zwar vollständig implementiert, aber nicht live
gegen echtes Outlook getestet. Eine funktional gleichwertige
In-Memory-Implementierung (`MockCalendarClient`) übernimmt automatisch, wenn
keine Zugangsdaten gesetzt sind, und wird von der gesamten Testsuite
verwendet.

## Absage: Auftrag zurück auf OFFEN, nicht ABGESAGT

Bei einer Terminabsage durch den Hersteller ist nicht die Wartung an sich
hinfällig, sondern nur der konkrete Termin. Die betroffenen
Wartungsaufträge werden deshalb auf den Status OFFEN zurückgesetzt (erneut
planbar), nicht auf ABGESAGT (das würde bedeuten, die Wartung entfällt
komplett).
