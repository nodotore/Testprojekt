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
