# Entscheidungen

## UC-001 – CD Musikfinder

**Architektur: PWA statt native iOS-App.**
`USE_CASES.md` empfahl ursprünglich eine native Swift/SwiftUI-App. Die
Implementierung erfolgt stattdessen als Progressive Web App
(`cd-musikfinder.html` + `js/cd-musikfinder.js`), analog zur bestehenden
`use-case-app.html`. Grund: In der genutzten Entwicklungsumgebung steht
kein macOS/Xcode zur Verfügung, eine native App könnte also nicht gebaut
oder getestet werden. Die PWA lässt sich dagegen tatsächlich bauen,
automatisiert testen (Playwright/Chromium) und ist trotzdem ohne App
Store direkt vom iPhone aus über Safari → "Zum Home-Bildschirm"
installierbar. Vom Benutzer bestätigt (siehe Rückfrage vor Beginn der
Implementierung).

**Texterkennung (OCR): Tesseract.js, best effort, kein harter Offline-Zwang.**
Echte Offline-OCR ohne jede Internetverbindung würde bedeuten, eine
mehrere MB große Bibliothek fest in das Repository/den Cache
einzubetten. Stattdessen wird Tesseract.js beim ersten Einsatz von einem
CDN nachgeladen; der Service Worker cached alle dabei geladenen
Ressourcen (auch fremder Herkunft), sodass ein zweiter Einsatz auch
offline funktioniert. Schlägt das Laden fehl (keine Verbindung beim
allerersten Einsatz, CDN nicht erreichbar), wird ohne Texterkennung
fortgefahren - die Kernfunktionen (Fotografieren, Angaben erfassen,
suchen, sortieren) bleiben davon unberührt und funktionieren immer
offline. Damit ist die nichtfunktionale Anforderung "Kernfunktion auch
ohne Internetverbindung nutzbar" erfüllt, ohne die optionale
Komfortfunktion OCR unnötig einzuschränken.

**Sortierung/"logische Reihenfolge": alphabetisch nach Regal, dann Interpret, dann Album.**
Der Use Case verlangt eine automatische, für Menschen nachvollziehbare
Sortierung samt Vorschlag, wie eine CD schnell zu finden ist. Eine echte
KI-Klassifizierung wäre hier weder nötig noch zuverlässiger als eine
einfache, transparente alphabetische Sortierung passend zu einem
physischen Regal. Jede CD bekommt daraus einen Vorschlagstext
("Regal X, Platz Y von Z, zwischen A und B").

**Speicherung: IndexedDB statt localStorage.**
Fotos werden als `Blob` gespeichert; localStorage ist dafür ungeeignet
(Textformat, kleines Kontingent). IndexedDB erlaubt das direkte Ablegen
von `Blob`-Objekten und reicht für die geforderte Offlinefähigkeit und
Datensicherheit aus.

**Automatisches Backup = Rückgängig-Verlauf.**
Vor jedem Löschen/Überschreiben einer CD wird die vorherige Version in
einem eigenen IndexedDB-Store abgelegt (auf die letzten 10 Einträge
begrenzt). Dieselbe Liste dient sowohl als Ein-Klick-"Rückgängig" auf dem
Startbildschirm als auch als browsbare Liste automatischer Sicherungen
unter "Backup & Regale". Zusätzlich kann die komplette Sammlung jederzeit
manuell als JSON-Datei exportiert werden.

**Ein gemeinsamer Service Worker für die ganze Website.**
Statt eines zweiten Service Workers mit eigenem Scope (Scope-Konflikte
mit `sw.js`, das bereits die gesamte Origin "/" bedient) wurde `sw.js`
erweitert: Er cached jetzt das App-Shell aller Seiten (Website +
Use-Case-App + CD Musikfinder) und generisch alle weiteren
GET-Ressourcen (inkl. Cross-Origin-Antworten der optionalen
Texterkennung), damit sie nach dem ersten Laden auch offline verfügbar
sind. Der CD Musikfinder bleibt davon unabhängig: eigene HTML/CSS/JS-
Dateien, eigenes Manifest, eigene IndexedDB-Datenbank - keine
funktionale Kopplung an die bestehende Website.
