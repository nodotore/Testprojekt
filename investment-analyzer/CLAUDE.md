# CLAUDE.md — Investment-Analysator

Projektstamm für den in `AUFTRAG.md` beschriebenen Investment-Analysator.
Dieses Verzeichnis (`investment-analyzer/`) ist ein eigenständiges
Unterprojekt innerhalb des Repos `nodotore/Testprojekt` (siehe
`DECISIONS.md` → ADR-1 zur Begründung). Alle Pfadangaben in diesem
Dokumentensatz sind relativ zu diesem Verzeichnis, sofern nicht anders
angegeben.

## Vor jeder Arbeitssitzung lesen (Pflicht, siehe Auftrag §13)

In dieser Reihenfolge:

1. `AUFTRAG.md` — der unveränderte Originalauftrag (Quelle der Wahrheit)
2. `PROGRESS.md` — was ist fertig, was läuft gerade
3. `NEXT_STEPS.md` — was als Nächstes zu tun ist
4. `TODO.md` — offene Einzelaufgaben und offene Nutzerentscheidungen
5. `DECISIONS.md` — bereits getroffene Architektur-/Designentscheidungen (nicht widersprechen, sondern per neuem ADR-Eintrag ändern)
6. `DATA_SOURCES.md`, `METHODOLOGY.md`, `SECURITY.md` je nach Aufgabe

Nach jeder relevanten Änderung: `PROGRESS.md`, `TODO.md`, `DECISIONS.md`,
`CHANGELOG.md`, `NEXT_STEPS.md` aktualisieren (Auftrag §4/§13). Ein
Sitzungs- oder Tokenende darf keinen Wissensverlust verursachen — die
nächste Session muss allein aus diesen Dateien nahtlos weiterarbeiten
können.

## Aktueller Stand

**Milestone 0–8 (aller ursprüngliche Auftragsplan) abgeschlossen.**
Ehrliche Abnahmebewertung gegen alle neun Auftrag-§15-Kriterien:
`ABNAHME.md`. Bedienungsanleitung für Endnutzer: `BENUTZERHANDBUCH.md`.
**Laufende Erweiterung darüber hinaus:** Ausbau der zehn Auftrag-§10-
Oberflächenseiten (aktuell fertig: „Start/Datenstatus", „Marktscreener",
„Kandidaten-Rangliste", „Unternehmensdetail mit Quellenleiste",
„Peer-Vergleich", „DCF- und Szenarioanalyse", „Nachrichten/Ereignisse",
„Watchlist/Portfolio"; zwei weitere offen, siehe `NEXT_STEPS.md`).
Details/offene Punkte: `PROGRESS.md`/`TODO.md`/`NEXT_STEPS.md`.

## Nicht verhandelbare Leitplanken

- **Keine erfundenen Zahlen.** Jede im UI/Report gezeigte Kennzahl muss
  auf einem gespeicherten Quellenobjekt oder einer nachvollziehbaren
  Formel beruhen (Auftrag §11). Niemals Platzhalterzahlen verwenden, die
  wie echte aktuelle Kurse/Kennzahlen aussehen (Auftrag §16, letzter
  Satz).
- **Keine Kaufempfehlung, kein Autotrading.** Nur Research-/
  Simulationsmodus (Auftrag §1, §12). Verbotene Begriffe: „sicherer
  Kauf", „garantierter Gewinn" (Auftrag §7).
- **Point-in-time-Prinzip.** Keine Daten verwenden, die zum
  Analysezeitpunkt noch nicht bekannt waren (Auftrag §5, §9).
- **Belegpflicht.** Mindestens zwei unabhängige Quellen für kritische
  Angaben; bei Widerspruch beide Werte zeigen (Auftrag §3).
- **Fail loud, nicht silent.** Fällt eine Quelle aus, erscheint ein
  klarer Fehler statt eines veralteten Werts, der als aktuell ausgegeben
  wird (Auftrag §4, §15).
- **Deterministisches Scoring.** Scores/Ranglisten entstehen aus Code,
  nicht aus einem KI-Texturteil. Die KI fasst nur zusammen (Auftrag §8a).

## Modulgrenzen (verbindlich ab Milestone 1)

`src/investment_analyzer/{connectors, normalization, entity_resolution,
fundamentals, valuation, news, risk, scoring, backtesting, reports,
ingestion, ui, audit}` — siehe `DECISIONS.md` → ADR-3 für Details und
Dateibesitz je Agentenrolle. `ingestion/` (neu, siehe ADR-26) bindet
`connectors/`, `entity_resolution/` und `normalization/` für den
Marktscreener zusammen — erzeugt selbst keine neuen Werte.

## Agentenkoordination (Auftrag §4)

- Vor Parallelisierung: Schnittstellen, Dateien und Abnahmekriterien pro
  Agent schriftlich festlegen (siehe `PLAN.md` je Milestone).
- Nie zwei Agenten unkoordiniert an derselben Datei.
- Jeder Agent dokumentiert: Auftrag, Ergebnis, geänderte Dateien, Tests,
  offene Risiken, nächster Schritt — als Eintrag in `PROGRESS.md`.
- Agentenergebnisse sind Vorschläge bis der Hauptagent Review + Tests
  abgeschlossen hat; erst danach Merge in den Hauptstand.
- Widersprüchliche Ergebnisse: Quellen und Rechenweg vergleichen, nicht
  still entscheiden — Konflikt in `DECISIONS.md` dokumentieren und
  auflösen.

## Rollen (bei Bedarf als Subagenten einzusetzen)

`project-orchestrator` (Hauptagent/diese Session), `data-source-agent`,
`financial-analysis-agent`, `backend-agent`, `frontend-agent`,
`backtest-agent`, `security-reviewer`, `test-agent`. Rollenbeschreibung:
siehe `AUFTRAG.md` §4.
