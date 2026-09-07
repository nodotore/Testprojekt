# TODO — Investment-Analysator

## Milestone 0

- [x] Auftrag vollständig gelesen und als `AUFTRAG.md` referenziert
- [x] Fragenliste erstellt (`MILESTONE_0.md`)
- [x] Quellen-/Lizenzmatrix + Kostenvarianten erstellt (`DATA_SOURCES.md`)
- [x] Architekturentscheidung dokumentiert (`DECISIONS.md`)
- [x] Verbindlicher Implementierungsplan erstellt (`PLAN.md`)
- [x] Methodik-Planungsstand dokumentiert (`METHODOLOGY.md`)
- [x] Sicherheitsrichtlinie-Planungsstand dokumentiert (`SECURITY.md`)
- [x] Nutzer beantwortet die blockierenden Fragen A1–A4 in
      `MILESTONE_0.md` (2026-09-07)
- [ ] Nutzer gibt Milestone 1 ausdrücklich frei

## Milestone 1 — Grundgerüst (abgeschlossen)

- [x] `pyproject.toml` + Tooling-Setup (ruff, mypy, pytest)
- [x] Paketstruktur gemäß ADR-3/ADR-11 anlegen
- [x] Konfigurationssystem für Nutzerprofil (Auftrag §2)
- [x] SecretStore (Keyring + verschlüsselte Datei)
- [x] Datenbankschema + Alembic-Migrationen (gegen SQLite getestet)
- [x] Logging + Audit-Log-Grundgerüst
- [x] Streamlit-Startseite + Ersteinrichtungsdialog
- [x] Windows-Startskripte (`start.ps1`/`start.bat`)
- [x] Grundgerüst-Tests (50 Tests grün, ruff+mypy fehlerfrei)
- [ ] PostgreSQL-Migrationspfad gegen echte Instanz testen (nachholen,
      sobald verfügbar — siehe `PROGRESS.md` „Offene Risiken")
- [ ] Streamlit-Oberfläche in echtem Browser bedienen (Sandbox hatte nur
      Headless-/HTTP-Verifikation)

## Milestone 2 — Datenbeschaffung (nächster Schritt)

- [ ] Connector-Basisklasse (Timeout, Retry+Backoff, Rate Limiting,
      Cache, Validierung, Fehlerprotokoll, Lizenzhinweis)
- [ ] Connector A: SEC EDGAR (Meldungen, USA)
- [ ] Connector B: Alpha Vantage Free (Marktdaten)
- [ ] SSRF-Schutz + URL-Allowlist je Connector
- [ ] Normalisierung (Einheiten, Währung, Geschäftsjahr, Splits/Dividenden)
- [ ] Entity Resolution (Ticker/ISIN/LEI → interne Entity-ID) befüllen
- [ ] Tests: Cache, Rate-Limit-Einhaltung, simulierter Quellenausfall

## Spätere Milestones

Siehe `PLAN.md` für Milestone 3–8; werden hier erst als Einzelaufgaben
aufgeschlüsselt, wenn die jeweilige Milestone beginnt.
