# Changelog

## Unreleased
- Neue Windows-Startroutine `Alle-Projekte-starten.ps1`/`.bat` (+ Gegenstück
  `Alle-Projekte-stoppen.ps1`/`.bat`): startet Website, PWAs und den
  Investment-Analysator mit einem Aufruf; erkennt bereits laufende
  Server über den belegten Port. Optionaler Windows-Autostart über
  `scripts/windows/Autostart-einrichten.ps1` (Verknüpfung im
  persönlichen Autostart-Ordner, kein Admin nötig).
- Dokumentiert, wie einzelne Projekte auf einen USB-Stick mitgenommen
  und auf einem anderen Rechner betrieben werden können (README.md,
  investment-analyzer/README.md → „Portabler Einsatz").
- Bugfix: `js/cd-musikfinder.js` enthielt zwei eingebettete NUL-Bytes
  (`"\x00ohne-regal"` statt `"ohne-regal"`), vermutlich ein
  Encoding-Artefakt aus einem früheren Bearbeitungsschritt — entfernt.
- UC-001 „CD Musikfinder" implementiert: neue PWA (`cd-musikfinder.html`,
  `js/cd-musikfinder.js`, `css/cd-musikfinder.css`,
  `manifest-cd-musikfinder.webmanifest`) zum Fotografieren von
  CD-Hüllen, optionaler Texterkennung, automatischer Sortierung,
  Fundort-Vorschlag, Suche nach Interpret/Songtitel, Rückgängig-Funktion
  und JSON-Backup-Export. `sw.js` erweitert, damit auch diese neue Seite
  offlinefähig ist. Navigationslink auf allen bestehenden Seiten ergänzt.
- Use Case UC-001 „CD Musikfinder" erfasst und in `USE_CASES.md`
  dokumentiert; zugehörigen Implementierungs-Prompt in
  `USE_CASE_PROMPTS.md` abgelegt.
