# Investment-Analysator

Lokal startbares Research-/Analyseprogramm mit deutscher Oberfläche zur
systematischen Recherche und zum Vergleich börsennotierter Unternehmen.
**Kein Anlageberatungs- oder Autotrading-Tool** — reiner Research-/
Simulationsmodus, siehe Hinweis unten und `SECURITY.md`.

> **Projektstand:** Milestone 1 (Grundgerüst). Es sind noch keine
> Datenquellen angebunden (folgt in Milestone 2) — die Oberfläche zeigt
> daher bewusst noch keine Analyseergebnisse, sondern nur den
> tatsächlichen (leeren) Datenstatus. Siehe `PROGRESS.md`/`PLAN.md`.

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
├── MILESTONE_0.md          Fragenliste + Nutzerantworten
├── start.ps1 / start.bat   Windows-Startskripte
├── scripts/run-tests.ps1   Test-/Lint-/Typprüfungsskript
├── alembic/                Datenbankmigrationen
├── src/investment_analyzer/
│   ├── config/              Nutzerprofil, App-Einstellungen, Secret-Store
│   ├── db/                  SQLAlchemy-Grundgerüst
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
