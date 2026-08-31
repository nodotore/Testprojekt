# Use-Case-Prompts

Automatisch aus `USE_CASES.md` abgeleitete Implementierungs-Prompts für
Claude Code. Format und Ablauf: siehe
`.claude/skills/use-case-generator/SKILL.md`, Abschnitt 12.

---

## IMPLEMENTIERUNG UC-001

### Ziel
Implementiere folgenden Use Case (CD Musikfinder):

Eine private iOS-App, mit der CD-Hüllen per Kamera fotografiert werden.
Aus den Fotos wird der Text (Interpret, Titel, Songtexte) erkannt und in
einer Liste/Datenbank abgelegt. Die App sortiert und ordnet neue Aufnahmen
automatisch ein und schlägt vor, wie eine gesuchte CD am schnellsten zu
finden ist. Der Benutzer kann per Suchleiste nach Interpret oder Songtitel
suchen und bekommt angezeigt, auf welcher CD sich das gesuchte Lied
befindet. Die App muss offlinefähig sein, darf erfasste Daten nie
verlieren, muss vor kritischen Änderungen automatisch sichern, laufende
Vorgänge fortsetzen können und Änderungen rückgängig machen können.

Vollständige Details, Ablauf, Fehlerfälle und die technische Analyse stehen
in `USE_CASES.md` unter UC-001.

### Bestehendes Projekt
Lies zuerst:
- CLAUDE.md (falls vorhanden)
- PLAN.md (falls vorhanden)
- PROGRESS.md (falls vorhanden)
- TODO.md (falls vorhanden)
- DECISIONS.md (falls vorhanden)
- CHANGELOG.md (falls vorhanden)
- NEXT_STEPS.md (falls vorhanden)
- USE_CASES.md

Analysiere anschließend den bestehenden Code.

**Wichtiger Hinweis:** Dieses Repository enthält aktuell ausschließlich die
statische Nordlicht-Studio-Website (`index.html`, `leistungen.html`,
`kontakt.html`, `use-case-app.html`, `css/`, `js/`) sowie die
Use-Case-Dokumentation. Es existiert kein iOS-App-Projekt und kein Code,
der für UC-001 wiederverwendet werden könnte. Der CD Musikfinder ist ein
komplett neues, eigenständiges Projekt (z. B. ein separates Xcode-Projekt
in einem eigenen Unterordner oder Repository) und hat keine funktionale
Abhängigkeit zur bestehenden Website. Vor der Umsetzung mit dem Benutzer
klären, wo/als was das neue App-Projekt angelegt werden soll, falls das
nicht eindeutig ist.

### Anforderungen
- Kamera-Erfassung von CD-Hüllen mit Bildqualitätsprüfung; bei schlechter
  Qualität Hinweis, das Foto erneut aufzunehmen
- Bestätigung durch den Benutzer nach jeder Aufnahme, ob das Bild
  akzeptiert wird
- Texterkennung (OCR) der Bilder: Interpret, Titel/Liedtext werden aus dem
  Bild in Text umgewandelt
- Automatische, KI-gestützte Sortierung/Ablage der erkannten Daten,
  inklusive automatischer Neueinsortierung bei jedem neuen Foto
- Vorschlag, wie eine gesuchte CD schnell zu finden ist
- Suchleiste: Suche nach Interpret ODER Songtitel
- Ergebnisanzeige: Name des Interpreten, Liedtext, zugehörige CD
- Kamera-Button und ein Button für manuelle Textangabe (Alternative zur
  Kameraaufnahme)
- Benutzer kann Ordner/Ablagebereiche auswählen
- Automatisches Backup vor kritischen Änderungen
- Fortschrittsanzeige während der Verarbeitung (OCR, Sortierung)
- Hintergrundverarbeitung für Sortierung/OCR
- Abgebrochene Vorgänge können fortgesetzt werden
- Änderungen können rückgängig gemacht werden
- Bereits aufgenommene Daten dürfen nie verloren gehen — sichere
  Speicherung erforderlich
- Meldung „Leider keine Daten vorhanden“, wenn keine Datei/kein Treffer
  vorliegt
- iOS-Berechtigung für Kamera/Fotobibliothek anfragen und definiertes
  Verhalten bei Ablehnung umsetzen
- Kernfunktion (Erfassen, Sortieren, Suchen) muss ohne Internetverbindung
  funktionieren

### Akzeptanzkriterien
- Wenn alle CDs archiviert sind, findet man sie über die App-Suche schnell
  wieder (Interpret oder Songtitel → korrekte CD wird angezeigt)
- Schlechte Fotoqualität wird erkannt und der Benutzer wird zur erneuten
  Aufnahme aufgefordert
- Fehlende Daten führen zur Meldung „Leider keine Daten vorhanden“
- Ein abgebrochener Erfassungs-/Sortiervorgang lässt sich fortsetzen
- Änderungen (z. B. an der Sortierung oder Zuordnung) lassen sich rückgängig
  machen
- Bereits aufgenommene Daten gehen unter keinen Umständen verloren und sind
  sicher abgespeichert (inkl. automatischem Backup vor kritischen
  Änderungen)

### Sicherheitsregel
Bestehende funktionierende Funktionen dürfen nicht beschädigt werden.
Vor Änderungen prüfen, welche bestehenden Komponenten betroffen sind. Da
UC-001 keine bestehende Funktionalität dieses Repositories berührt, darf
die Umsetzung insbesondere die bestehende Website (`index.html`,
`leistungen.html`, `kontakt.html`, `use-case-app.html`, `css/`, `js/`,
`sw.js`, `manifest.webmanifest`) nicht verändern.

### Implementierung
1. Projekt analysieren.
2. Implementierungsplan erstellen (inkl. Klärung, wo das neue App-Projekt
   im Repository/Workspace angelegt wird).
3. Abhängigkeiten prüfen.
4. Änderungen durchführen.
5. Tests durchführen.
6. Fehler korrigieren.
7. Akzeptanzkriterien überprüfen.
8. Projektdokumentation aktualisieren.
9. Fortschritt sichern.
10. Nächste Schritte dokumentieren.
