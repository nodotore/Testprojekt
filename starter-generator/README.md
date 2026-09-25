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
| `Starter-erstellen.bat -Force` | vorhandene `Starten.exe` neu erstellen |
| `Starter-erstellen.bat -Root "D:\Projekte"` | anderen Grundordner verwenden |
| `Starter-erstellen.bat -ExeName "Projekt.exe"` | anderen EXE-Namen verwenden |
| `Starter-erstellen.bat -Tiefe 6` | tiefer verschachtelte Ordner durchsuchen (Standard: 4) |

Neue Projekte hinzugekommen? Einfach die `.bat` erneut ausführen –
vorhandene EXEs bleiben unverändert, nur neue werden angelegt.

## Wie wird erkannt, wie ein Projekt startet?

Die Unterordner des Grundordners werden bis zu 4 Ebenen tief
durchsucht (z. B. `Y:\claude\projekt\MeinProjekt`). Ist ein Ordner als
Projekt erkannt, wird darunter nicht weiter gesucht. Ordner mit `.git`,
`pyproject.toml`, `requirements.txt`, `package.json` oder einer
`.sln`-Datei gelten auch ohne Startdatei als Projekt und erscheinen dann
als „übersprungen“ in der Tabelle.

Pro Ordner wird in dieser Reihenfolge gesucht:

1. `start.ps1`, `starten.ps1`, `run.ps1`, `launch.ps1` → PowerShell-Skript
2. `start.bat`, `starten.bat`, `run.bat` (oder `.cmd`) → Batch-Datei
3. genau ein einziges `.ps1`- bzw. `.bat`/`.cmd`-Skript im Ordner
4. `package.json` mit `start`- oder `dev`-Skript → `npm start` (beim
   ersten Start automatisch `npm install`)
5. `app.py`, `main.py`, `streamlit_app.py`, `run.py`, `start.py`,
   `gui.py`, `<Ordnername>.py` oder genau eine `.py`-Datei → Python.
   Enthält die Datei `import streamlit`, wird sie mit
   `python -m streamlit run` gestartet. Eine projekteigene virtuelle
   Umgebung (`.venv`, `venv`, `env`) wird automatisch bevorzugt.
6. `index.html` (oder genau eine `.html`-Datei) → im Standardbrowser öffnen

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
