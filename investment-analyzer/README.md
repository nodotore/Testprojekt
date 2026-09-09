# Investment-Analysator

Lokal startbares Research-/Analyseprogramm mit deutscher Oberfläche zur
systematischen Recherche und zum Vergleich börsennotierter Unternehmen.
**Kein Anlageberatungs- oder Autotrading-Tool** — reiner Research-/
Simulationsmodus, siehe Hinweis unten und `SECURITY.md`.

> **Projektstand:** Alle acht Milestones (Auftrag §14) implementiert,
> getestet und einem zweistufigen Security-Review inkl. unabhängiger
> Prüfung unterzogen (482 automatisierte Tests). **Noch nicht
> vollständig abnahmefähig** im strengen Sinn von Auftrag §15 — eine
> ehrliche, kriterienweise Bewertung mit den verbleibenden offenen
> Punkten (v. a.: kein Internetzugang in dieser Entwicklungsumgebung,
> daher keine Verifikation mit echten Marktdaten; erst vier von zehn
> Oberflächenseiten gebaut, siehe `TODO.md`) steht in `ABNAHME.md`. Ausführliche
> Bedienungsanleitung: `BENUTZERHANDBUCH.md`. Details:
> `PROGRESS.md`/`TODO.md`/`NEXT_STEPS.md`.

## Wichtiger Hinweis

Dieses Programm liefert allgemeine Information im Research-/
Simulationsmodus — **keine individuelle Anlage-, Steuer- oder
Rechtsberatung** und keine Kauf-/Verkaufsempfehlung. Es handelt keine
Wertpapiere automatisch. Investitionen können bis zum Totalverlust des
eingesetzten Kapitals führen.

## Voraussetzungen

- Windows 10/11
- [Python 3.12 oder neuer](https://www.python.org/downloads/) (beim
  Installer „Add python.exe to PATH" aktivieren)

## Start

Im Windows Explorer `start.bat` doppelklicken, oder in PowerShell:

```powershell
.\start.ps1
```

Das Skript legt beim ersten Start automatisch eine virtuelle
Python-Umgebung (`.venv`) an, installiert die Abhängigkeiten, führt die
Datenbankmigrationen aus und öffnet danach die Streamlit-Oberfläche
(normalerweise unter `http://localhost:8501`).

Für die Entwicklungsabhängigkeiten (Tests, Linter):

```powershell
.\start.ps1 -Dev
```

Ein Doppelklick-Installer (`.exe`/`.msi`) wird bewusst NICHT
mitgeliefert — die Entwicklungsumgebung dieses Projekts hat keinen
Zugriff auf Windows-Build-Werkzeuge, um ein solches Installationspaket
zu erzeugen und zu testen (siehe `PROGRESS.md`/`BENUTZERHANDBUCH.md`).
Start und Abhängigkeitsinstallation laufen stattdessen vollständig über
`start.ps1`/`start.bat`.

## Datensicherung

```powershell
.\scripts\backup-database.ps1
.\scripts\restore-database.ps1 <Sicherungsdatei>
```

`start.ps1` sichert die Datenbank vor jeder Migration automatisch
(überspringbar mit `-NoBackup`). Details: `BENUTZERHANDBUCH.md`,
Abschnitt „Datensicherung".

## Tests ausführen

```powershell
.\scripts\run-tests.ps1
```

Führt `ruff` (Lint), `mypy` (Typprüfung) und die vollständige
`pytest`-Testsuite aus.

## Projektstruktur

```
investment-analyzer/
├── AUFTRAG.md            Unveränderter Originalauftrag (verbindliche Referenz)
├── CLAUDE.md              Leitplanken/Modulgrenzen für Weiterentwicklung
├── PLAN.md                Verbindlicher Implementierungsplan (Milestones 0–8)
├── PROGRESS.md            Aktueller Fortschritt
├── TODO.md                 Offene Aufgaben
├── DECISIONS.md            Architekturentscheidungen (ADRs)
├── CHANGELOG.md            Änderungsprotokoll
├── NEXT_STEPS.md           Nächste Schritte
├── DATA_SOURCES.md         Quellen-/Lizenzmatrix, Kostenvarianten
├── METHODOLOGY.md          Kennzahlen-/Bewertungs-/Scoring-Methodik
├── SECURITY.md             Sicherheitsrichtlinie
├── ABNAHME.md              Abnahme-Checkliste gegen Auftrag §15
├── MILESTONE_0.md          Fragenliste + Nutzerantworten
├── BENUTZERHANDBUCH.md      Bedienungsanleitung für Endnutzer
├── start.ps1 / start.bat   Windows-Startskripte
├── scripts/run-tests.ps1   Test-/Lint-/Typprüfungsskript
├── scripts/backup-database.ps1    Datenbank sichern
├── scripts/restore-database.ps1   Datenbank wiederherstellen
├── alembic/                Datenbankmigrationen
├── src/investment_analyzer/
│   ├── config/              Nutzerprofil, App-Einstellungen, Secret-Store
│   ├── db/                  SQLAlchemy-Grundgerüst, Sicherung/Wiederherstellung
│   ├── entity_resolution/   Stabile Unternehmens-Identität (Entity, Ticker/ISIN/LEI)
│   ├── connectors/          Datenquellen (ab Milestone 2)
│   ├── normalization/       Provenienzbehaftete Datenpunkte, Normalisierung
│   ├── fundamentals/        Kennzahlenberechnung (ab Milestone 3)
│   ├── valuation/           Multiples, DCF (ab Milestone 4)
│   ├── news/                 Nachrichtenanalyse (ab Milestone 5)
│   ├── risk/                  Risiken/Warnsignale
│   ├── scoring/               Erklärbares Scoring (ab Milestone 4)
│   ├── backtesting/           Point-in-time-Backtests (ab Milestone 7)
│   ├── reports/                Excel/PDF/JSON-Export (ab Milestone 6)
│   ├── audit/                  Logging, Audit-Log
│   └── ui/                     Streamlit-Oberfläche
└── tests/                    Spiegelt die Paketstruktur
```

Details zu Modulgrenzen und Architekturentscheidungen: `DECISIONS.md`.
Details zum Gesamtauftrag: `AUFTRAG.md`.
