# Starter-Generator – eine `Starten.exe` für jedes Projekt

Erstellt in jedem Projektordner unter einem Grundordner (Standard:
`Y:\claude`) eine **`Starten.exe`**. Ein Doppelklick darauf startet das
Projekt, ganz ohne PowerShell-Fenster zu öffnen oder Befehle einzugeben.

## Einrichtung (einmalig)

1. Den Ordner `starter-generator` nach `Y:\claude\starter-generator`
   kopieren (er wird selbst übersprungen).
2. **`Starter-erstellen.bat` doppelklicken.**
3. Am Ende zeigt eine Tabelle für jedes Projekt, wie es gestartet wird und
   ob die EXE erstellt wurde.

Danach liegt in jedem erkannten Projekt eine `Starten.exe`.

Weitere Aufrufe (in der Eingabeaufforderung oder PowerShell):

| Aufruf | Wirkung |
|---|---|
| `Starter-erstellen.bat -Vorschau` | nur anzeigen, was erkannt würde |
| `Starter-erstellen.bat -Force` | auch eine fremde Datei namens `Starten.exe` überschreiben |
| `Starter-erstellen.bat -Ausschliessen Claude_Backup,Alt` | diese Ordner nicht durchsuchen (Standard: `Claude_Backup`) |
| `Starter-erstellen.bat -Root "D:\Projekte"` | anderen Grundordner verwenden |
| `Starter-erstellen.bat -ExeName "Projekt.exe"` | anderen EXE-Namen verwenden |
| `Starter-erstellen.bat -Tiefe 6` | tiefer verschachtelte Ordner durchsuchen (Standard: 4) |

Neue Projekte hinzugekommen? Einfach die `.bat` erneut ausführen –
neue EXEs werden angelegt, vorhandene auf den neuesten Stand gebracht.
In ausgeschlossenen Ordnern (Backups) werden früher erzeugte
`Starten.exe` wieder entfernt.

## Python-Umgebung (.venv) – automatisch

Eine `.venv` merkt sich den Pfad des Python, mit dem sie erstellt wurde.
Nach einem Umzug auf einen anderen Rechner/Benutzer oder einer
Python-Neuinstallation ist sie deshalb kaputt („did not find executable
at …“). Die `Starten.exe` erkennt das und kümmert sich selbst darum:

- **Python-Projekte** (`requirements.txt`/`pyproject.toml`): fehlende
  oder defekte `.venv` wird angelegt, die Pakete werden installiert –
  erneut, sobald sich `requirements.txt`/`pyproject.toml` ändern.
  Braucht das Projekt Playwright, wird auch der Browser installiert.
- **Projekte mit eigenem Startskript**, das die `.venv` selbst anlegt:
  eine defekte `.venv` wird gelöscht, das Skript legt sie neu an.

Der erste Start eines Projekts dauert dadurch einige Minuten.

## Wenn ein Projekt nicht startet: `Diagnose.bat`

`Diagnose.bat` doppelklicken. Das Skript
- erstellt zuerst alle `Starten.exe` neu (also immer mit der aktuellen
  Werkzeug-Version),
- richtet je Projekt die Python-Umgebung ein, ohne Zeitlimit (höchstens
  30 Minuten je Projekt, `-EinrichtenMinuten`),
- erfasst die Umgebung (Python, Node.js, npm, git, PowerShell),
- startet danach jede `Starten.exe` einzeln für 20 Sekunden (ohne
  sichtbares Fenster und ohne Dateiauswahl-Dialog), zeichnet alle Ausgaben und Fehlermeldungen auf
  und beendet das Programm wieder,
- listet Projektordner ohne `Starten.exe` mit ihrem Inhalt auf.

Der Bericht landet in `Diagnose.txt` im Werkzeug-Ordner. Er enthält nur
Datei- und Ordnernamen sowie die Programmausgaben. Vor dem Weitergeben
kurz durchsehen, ob darin etwas Vertrauliches steht.
`Diagnose.bat -Sekunden 40` lässt langsame Programme länger laufen,
`Diagnose.bat -OhneStarttest` startet gar nichts.

## Wie wird erkannt, wie ein Projekt startet?

Die Unterordner des Grundordners werden bis zu 4 Ebenen tief
durchsucht (z. B. `Y:\claude\projekt\MeinProjekt`). Ist ein Ordner als
Projekt erkannt, wird darunter nicht weiter gesucht. Ordner mit `.git`,
`pyproject.toml`, `requirements.txt`, `package.json` oder einer
`.sln`-Datei gelten auch ohne Startdatei als Projekt und erscheinen dann
als „übersprungen“ in der Tabelle.

Pro Ordner wird in dieser Reihenfolge gesucht:

1. `start.ps1`, `starten.ps1`, `run.ps1`, `launch.ps1` oder genau ein
   anderes `.ps1`-Skript → PowerShell-Skript
2. `start.bat`, `starten.bat`, `run.bat` (oder `.cmd`) oder genau eine
   andere `.bat`/`.cmd` → Batch-Datei

   Hilfsskripte (`build…`, `publish…`, `install…`, `exe_bauen…` usw.) und
   Platzhalter-Skripte („Kein automatischer Startbefehl hinterlegt“)
   zählen nicht.
3. `package.json` mit `start`- oder `dev`-Skript → `npm start` (beim
   ersten Start automatisch `npm install`)
4. Python, in dieser Reihenfolge:
   - `app.py`, `main.py`, `streamlit_app.py`, `run_app.py`, `run.py`,
     `start.py`, `gui.py`, `<Ordnername>.py` (Streamlit wird erkannt)
   - ein Paket mit `__main__.py` (auch unter `src\`) → `python -m paket`
   - ein Einstiegspunkt aus `pyproject.toml` (`[project.scripts]`)
   - ein einziges Paket (auch unter `src\`) mit `main.py`/`app.py`/`gui.py`/`cli.py`
     → `python -m paket.main`
   - `app\main.py` bzw. `src\main.py` → `python -m app.main`
   - genau eine `.py`-Datei (ohne `test_…`, `scratch…`, `setup.py`)
5. `index.html` (oder genau eine `.html`-Datei) → im Standardbrowser öffnen
6. genau eine fertige `.exe` in `Programm\` oder `dist\` → diese starten

Erwartet ein Batch-/PowerShell-Skript eine Datei (`%1` bzw. `$args[0]`,
z. B. „Video auf diese Datei ziehen“), fragt die `Starten.exe` beim
Doppelklick mit einem Dateiauswahl-Dialog danach. Dateien können auch
direkt auf die `Starten.exe` gezogen werden; sie werden weitergereicht.

Wird für einen Ordner keine Startart mehr erkannt, wird eine früher
erzeugte `Starten.exe` dort entfernt.

Liegt eine `.ico`-Datei im Projektordner, bekommt die EXE dieses Symbol.

Projekte, die „übersprungen“ werden, haben keine der obigen Dateien.
Am einfachsten legt man dort eine `start.ps1` oder `start.bat` mit dem
bisherigen Startbefehl an und führt den Generator erneut aus.

## Mitnehmen / Verschieben

Die EXE enthält **keine festen Pfade** – sie sucht alles relativ zu ihrem
eigenen Ordner. Ein Projektordner kann also samt `Starten.exe` auf einen
USB-Stick oder anderen Rechner kopiert werden. Dort müssen nur die
benötigten Programme (z. B. Python oder Node.js) installiert sein; fehlt
eines, zeigt die EXE einen Hinweis mit Download-Link an.

## Technik

- `Launcher.cs` ist die Vorlage der EXE; `Starter-erstellen.ps1` setzt
  Startart und Zieldatei ein und übersetzt sie mit dem C#-Compiler, der
  in jedem Windows 10/11 bereits enthalten ist
  (`C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe`).
  Es muss nichts installiert werden.
- Die EXE öffnet ein Konsolenfenster, damit Ausgaben sichtbar sind.
  Beendet sich das Programm mit einem Fehler, bleibt das Fenster offen,
  bis eine Taste gedrückt wird. Webseiten werden ohne Konsole geöffnet.
- PowerShell-Skripte werden mit `-ExecutionPolicy Bypass` gestartet, die
  Ausführungsrichtlinie muss also nicht geändert werden.

## Hinweis zu Virenscanner / SmartScreen

Selbst übersetzte, unsignierte EXEs werden von Windows Defender oder
SmartScreen gelegentlich beim ersten Start nachgefragt („Weitere
Informationen“ → „Trotzdem ausführen“). Der Quelltext liegt vollständig
in `Launcher.cs` vor.
