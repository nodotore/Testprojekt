# Testprojekt - Nordlicht Studio

Kleine, statische Test-Website ohne Build-Framework: reines HTML, CSS und
Vanilla-JavaScript. Dient als Beispiel für eine responsive, barrierefreie
Website mit Navigation samt Dropdown-Menü, Hamburger-Menü für mobile
Ansichten und einem clientseitig validierten Kontaktformular.

## Dateistruktur

```
Testprojekt/
├── index.html          Startseite (Hero-Bereich, Vorstellung, Call-to-Action)
├── leistungen.html      Leistungsseite mit drei Karten (Webdesign, Beratung, Support)
├── kontakt.html          Kontaktseite mit validiertem Formular (Demo, kein echter Versand)
├── css/
│   └── style.css         Gemeinsames Stylesheet für alle Seiten (responsive)
├── js/
│   └── script.js          Hamburger-Menü, Dropdown-Menü, Formularvalidierung
└── README.md
```

Alle drei Seiten teilen sich denselben Header (Logo, Navigation mit
Dropdown-Untermenü "Leistungen") und Footer.

## Website lokal öffnen/testen

### Option 1: Direktes Öffnen im Browser

Die Seiten funktionieren auch ohne Server. Einfach `index.html` doppelklicken
oder in PowerShell:

```powershell
Start-Process "index.html"
```

### Option 2: Lokalen Server starten (empfohlen, z. B. für saubere relative Pfade)

Mit Node.js (`serve`):

```powershell
npx serve .
```

Mit Python (falls installiert):

```powershell
python -m http.server 8000
```

Anschließend im Browser `http://localhost:3000` (bei `serve`) bzw.
`http://localhost:8000` (bei Python) öffnen.

## Deployment (GitHub Pages)

Jeder Push auf `master` deployt die Seite automatisch über
`.github/workflows/deploy-pages.yml` nach GitHub Pages. Die Seite ist
danach unter `https://<benutzername>.github.io/<repo-name>/` erreichbar
(Fortschritt und URL stehen im Actions-Tab bzw. unter
*Settings → Pages*).

Beim ersten Deployment aktiviert der Workflow GitHub Pages automatisch
(Source: *GitHub Actions*). Falls das in den Repository-Einstellungen
nicht erlaubt ist, einmalig manuell aktivieren: *Settings → Pages →
Build and deployment → Source → GitHub Actions*, danach den Workflow
erneut laufen lassen (Tab *Actions* → *Deploy GitHub Pages* → *Run
workflow*).

Alle Seiten verlinken ausschließlich relative Pfade (`css/…`, `js/…`,
`icons/…`), funktionieren also unverändert unter dem Pages-Unterpfad.
Das gilt auch für `use-case-app.html` und `cd-musikfinder.html`: Beide
Apps lassen sich auf dem iPhone direkt von der Pages-URL aus über
Safari → Teilen → "Zum Home-Bildschirm" installieren.

## CD Musikfinder (`cd-musikfinder.html`)

Eigenständige PWA zur Verwaltung einer physischen CD-Sammlung (siehe
UC-001 in `USE_CASES.md`). Funktioniert komplett offline und ohne
eigenes Backend:

- **Erfassen**: CD-Hülle über die Gerätekamera fotografieren (mit
  Bildqualitätsprüfung und Bestätigung vor dem Übernehmen) oder Angaben
  von Hand eingeben.
- **Texterkennung**: Best-effort-OCR über [Tesseract.js](https://github.com/naptha/tesseract.js),
  das beim ersten Einsatz von einem CDN nachgeladen wird. Ist keine
  Internetverbindung verfügbar oder schlägt das Laden fehl, wird ohne
  Texterkennung fortgefahren – die Kernfunktionen (Fotografieren,
  Speichern, Suchen) bleiben davon unberührt.
- **Ablage**: Alle Daten (inkl. Fotos als `Blob`) liegen in IndexedDB,
  ausschließlich auf dem Gerät. Die Sammlung wird automatisch nach
  Regal/Ablage, dann Interpret sortiert; zu jeder CD wird ein
  Fundort-Vorschlag berechnet.
- **Suche**: nach Interpret oder Songtitel, mit direkter Anzeige, auf
  welcher CD ein Song zu finden ist.
- **Datensicherheit**: Vor jedem Löschen/Überschreiben wird automatisch
  eine Sicherung angelegt (Rückgängig-Banner + browsbare Liste unter
  "Backup & Regale"); zusätzlich lässt sich die gesamte Sammlung als
  JSON-Datei exportieren. Ein unterbrochener Aufnahme-Vorgang (App
  geschlossen, bevor gespeichert wurde) wird beim nächsten Start zum
  Fortsetzen angeboten.

Technische Details, Anforderungen und offene Punkte: siehe `USE_CASES.md`
(UC-001) und `USE_CASE_PROMPTS.md`.

## Hinweise

- Das Kontaktformular in `kontakt.html` ist eine Demo: Es findet **kein**
  echter Versand statt. Bei erfolgreicher Validierung wird lediglich eine
  Erfolgsmeldung im Browser angezeigt (Nutzereingaben werden dabei
  ausschließlich über `textContent` eingefügt, nie über `innerHTML`, um
  XSS zu vermeiden).
- Die Navigation ist per Tastatur bedienbar: Hamburger-Button und
  Dropdown-Button besitzen `aria-expanded`, das Dropdown lässt sich mit
  Pfeiltaste/Escape steuern.
- Responsives Verhalten: Ab einer Breite von ca. 600px klappt die
  Navigation zu einem Hamburger-Menü zusammen; die Karten-Grids passen sich
  über Media Queries an Desktop (3 Spalten), Tablet (2 Spalten) und
  Smartphone (1 Spalte) an.
