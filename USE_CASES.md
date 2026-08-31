# Use Cases

Diese Datei enthält alle bestätigten Use Cases des Projekts, erfasst über
das Interview in `use-case-app.html` bzw. den Use-Case-Generator-Skill.

Format und Ablauf sind in `.claude/skills/use-case-generator/SKILL.md`
beschrieben. Zu jedem Use Case existiert ein passender
Implementierungs-Prompt in `USE_CASE_PROMPTS.md`.

---

## UC-001 – CD Musikfinder

### Ziel
Ich möchte eine App haben Genau das Gleiche wie zuvor besprochen.

### Benutzer
In erster Linie ich privat

### Ausgangssituation
_Keine besonderen Voraussetzungen erfasst._

### Auslöser
Einmal über die Kamera, um die ganzen Daten aufzunehmen, und anschließend per App auf dem Handy

### Normaler Ablauf
1. Benutzer startet: Einmal über die Kamera, um die ganzen Daten aufzunehmen, und anschließend per App auf dem Handy
2. Benutzer gibt Folgendes ein: Zum Suchen sollte man eigentlich entweder den Interpreten oder aber den Song selber eingeben können.
3. System führt automatisch aus: Die Sortierung und die Ablage, auch wenn neue Bilder von Hüllen dazu kommen, muss dies automatisch in die richtige Reihenfolge gebracht werden und auch ein Vorschlag gegeben werden, wie man es relativ schnell findet.
4. Danach müsste die KI diese in einer logischen Reihenfolge sortieren, damit man schnell die einzelnen CDs findet.
5. Währenddessen sieht der Benutzer: Eine CD am besten, die läuft
6. Ergebnis wird angezeigt bzw. gespeichert: Wenn alle CDs archiviert sind und man findet diese dann recht schnell über die App

### Ergebnis
Wenn alle CDs archiviert sind und man findet diese dann recht schnell über die App

### Alternative Abläufe
Keine besonderen alternativen Abläufe erfasst.

### Fehlerfälle
- Fehlerhafte Daten: Es soll eine Information erscheinen, zum Beispiel, das Foto erneut aufzunehmen, falls die Fotoqualität schlecht ist.
- Fehlende Dateien: Hier soll die Meldung kommen: Leider keine Daten vorhanden.
- Ein abgebrochener Vorgang wird fortgesetzt.
- Änderungen können rückgängig gemacht werden.
- Auf keinen Fall dürfen folgende Daten verloren gehen: Die bereits aufgenommenen Daten dürfen auf keinen Fall verloren gehen. Müssen sicher abgespeichert sein.

### Anforderungen
- Verwendete Dateien: Bilddateien, die dann anschließend in Text umgewandelt werden müssen
- Datenquelle: Durch die Fotografien von der Kamera des Smartphones
- Speicherort der Dateien: Anschließend sollen die Dateien in einer Art Liste liegen.
- Sichtbare Bildschirminhalte: Einmal das Kamerasymbol, um die ganzen Sachen aufzunehmen, sprich die Hüllenkommandos. Weiteren muss natürlich auch eine Art Suchleiste vorhanden sein, mit einer Ausgabe, wo man dieses Lied findet, und unter welcher CD.
- Benötigte Buttons/Aktionen: Kamera Button, Textangabe Button
- Angezeigte Informationen: Name des Interpreten, Liedtext und auf welcher CD ich diese finde
- Automatisch ausgeführte Aktionen: Die komplette Sortierung und das Zusammenstellen der einzelnen Lieder und das Finden der CDs
- Bestätigungspflichtige Aktionen: Einmal nach der Bildaufnahme, ob das Bild so gut ist
- Der Benutzer kann Ordner auswählen.
- Vor kritischen Änderungen wird automatisch ein Backup erstellt.
- Der Fortschritt wird während der Verarbeitung angezeigt.
- Das Programm trifft bestimmte Entscheidungen selbstständig.
- Es wird KI-Unterstützung eingesetzt.
- Das Programm lernt aus vorherigen Aktionen.
- Aufgaben laufen im Hintergrund.
- Zugriff auf Kamera bzw. Fotobibliothek erfordert eine iOS-Berechtigung. *(abgeleitet)*
- Verhalten bei verweigerter Berechtigung muss festgelegt werden. *(abgeleitet)*
- Kernfunktion muss auch ohne Internetverbindung nutzbar sein. *(abgeleitet)*

### Nichtfunktionale Anforderungen
- Bedienbarkeit: Die Bedienung ist auch ohne Anleitung weitgehend selbsterklärend.
- Offlinefähigkeit: Die Funktion ist auch ohne Internetverbindung nutzbar.
- Stabilität: Die Funktion läuft auch bei fehlerhaften Eingaben stabil weiter.

### Akzeptanzkriterien
- Der Use Case gilt als abgeschlossen, wenn: Wenn alle CDs archiviert sind und man findet diese dann recht schnell über die App
- Der Fehlerfall wird korrekt abgefangen: Fehlerhafte Daten: Es soll eine Information erscheinen, zum Beispiel, das Foto erneut aufzunehmen, falls die Fotoqualität schlecht ist.
- Der Fehlerfall wird korrekt abgefangen: Fehlende Dateien: Hier soll die Meldung kommen: Leider keine Daten vorhanden.
- Der Fehlerfall wird korrekt abgefangen: Ein abgebrochener Vorgang wird fortgesetzt.
- Der Fehlerfall wird korrekt abgefangen: Änderungen können rückgängig gemacht werden.
- Der Fehlerfall wird korrekt abgefangen: Auf keinen Fall dürfen folgende Daten verloren gehen: Die bereits aufgenommenen Daten dürfen auf keinen Fall verloren gehen. Müssen sicher abgespeichert sein.

### Priorität
SOLL

### Abhängigkeiten
Keine bekannt.

### Offene Punkte
- Was muss vorher schon vorhanden bzw. erledigt sein, damit es losgehen kann? (nicht beantwortet)
- Was macht der Benutzer zuerst? (nicht beantwortet)
- Welche Entscheidungen kann der Benutzer treffen? (nicht beantwortet)
- Welche Dateiformate gibt es? (nicht beantwortet)
- Welche Einstellungen soll der Benutzer verändern können? (nicht beantwortet)
- Welche Aktionen dürfen niemals automatisch ausgeführt werden? (nicht beantwortet)
- Was passiert bei einem Programmabsturz? (nicht beantwortet)
- Was passiert bei einem Neustart? (nicht beantwortet)
- Gibt es Abhängigkeiten zu anderen Funktionen, Use Cases oder externen Systemen? (nicht beantwortet)

### Technische Analyse (abgeleitet)

**Verhältnis zum bestehenden Projekt:** Dieses Repository (`Testprojekt`)
ist aktuell eine statische Website ohne Backend und ohne App-Code
(`index.html`, `leistungen.html`, `kontakt.html`, `use-case-app.html` +
`css/`, `js/`). Der CD Musikfinder ist eine eigenständige neue iOS-App und
hat keine Berührungspunkte mit dem bestehenden Website-Code — es gibt
nichts Vorhandenes, das dafür verändert werden müsste oder davon betroffen
wäre.

**Zu entwickelnde Komponenten (Empfehlung, da kein bestehender App-Code
existiert):**
- Native iOS-App (Swift/SwiftUI empfohlen wegen Kamera-, Vision- und
  Offline-Anforderungen; kein Backend nötig, da alles offlinefähig sein
  muss)
- Kamera-Erfassung von CD-Hüllen inkl. Bildqualitätsprüfung
  (Unschärfe-/Belichtungserkennung) vor der Bestätigung durch den Benutzer
- Texterkennung (OCR) der aufgenommenen Hülle, z. B. über das
  iOS-Vision-Framework (`VNRecognizeTextRequest`), rein on-device für
  Offlinefähigkeit
- Lokale Datenhaltung (z. B. SQLite/Core Data) für Interpret, Titel,
  Liedtext-Auszug und CD-Zuordnung je erfasstem Datensatz
- Automatische Sortier-/Ablagelogik, die bei jedem neuen Foto die
  bestehende Sammlung neu einordnet und einen "Fundort"-Vorschlag
  berechnet
- Suchfunktion über Interpret oder Songtitel mit Ergebnisanzeige
  (Interpret, Liedtext-Ausschnitt, zugehörige CD)
- Undo-/Wiederherstellungsmechanismus sowie automatisches Backup vor
  kritischen Änderungen (z. B. lokale Sicherungskopie der Datenbank)
- Fortschrittsanzeige für Hintergrundverarbeitung (OCR, Sortierung)
- Persistenz eines unterbrochenen Erfassungsvorgangs, damit dieser
  fortgesetzt werden kann

**Benötigte Schnittstellen/Berechtigungen:** Kamera-Zugriff (`NSCameraUsageDescription`),
optional Fotobibliothek-Zugriff, jeweils mit definiertem Verhalten bei
Ablehnung (Hinweistext + Verweis auf Einstellungen).

**Tests:** Unit-Tests für Sortier-/Suchlogik, UI-Tests für den
Kamera-→Bestätigung-→Speichern-Ablauf, Tests für Fehlerfälle (schlechte
Bildqualität, fehlende Daten, abgebrochener Vorgang, Wiederherstellung nach
Absturz).

**Risiken:** OCR-Erkennungsqualität bei schlecht lesbaren/verschlissenen
CD-Hüllen; Mehrdeutigkeit bei der automatischen Sortierung ohne
Benutzer-Feedback; Datenverlustrisiko bei fehlerhaftem Backup-Mechanismus.

**Offene technische Entscheidung:** Die in den offenen Punkten genannten
Fragen (Startzustand, Dateiformate, Einstellungen, Verhalten bei Absturz/
Neustart) sollten vor der Implementierung geklärt werden, da sie
Architektur und Datenmodell beeinflussen.
