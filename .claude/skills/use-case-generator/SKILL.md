---
name: use-case-generator
description: Strukturierter Anforderungsanalyst für neue oder bestehende Projekte. Führt den Benutzer durch ein geführtes Interview (Grundidee, Ablauf, Daten, UI, Automatisierung, Fehlerfälle, Priorität) und erzeugt daraus dokumentierte Use Cases in USE_CASES.md sowie passende Implementierungs-Prompts in USE_CASE_PROMPTS.md. Nutzen bei Formulierungen wie "Neuer Use Case", "Use Cases anzeigen", "Use Case umsetzen UC-XXX", "Use Cases prüfen", "Ändere Use Case X", oder wenn der Benutzer eine neue Idee/Funktion beschreibt, die zuerst sauber als Use Case erfasst werden soll, bevor programmiert wird.
---

# CLAUDE – USE-CASE-GENERATOR

## Ziel

Für jedes neue oder bestehende Projekt sollen die gewünschten Anwendungsfälle
strukturiert erfasst werden.

Claude darf die Use Cases nicht einfach erraten.

Claude führt zunächst ein verständliches Interview mit dem Benutzer durch,
wertet die Antworten aus und erstellt daraus:

- konkrete Use Cases
- Anforderungen
- Akzeptanzkriterien
- Sonderfälle
- technische Anforderungen
- Prioritäten
- daraus abgeleitete Entwicklungsaufgaben
- fertige Prompts für Claude Code

Die Ergebnisse werden dauerhaft im Projekt gespeichert.

---

## 1. Dateien

Im Hauptverzeichnis des jeweiligen Projekts folgende Dateien verwenden:

**USE_CASES.md**
Enthält alle bestätigten Use Cases.

**USE_CASE_PROMPTS.md**
Enthält die daraus automatisch erzeugten Claude-Code-Prompts.

Falls die Dateien noch nicht existieren, automatisch anlegen.

Bestehende Inhalte niemals ungeprüft überschreiben. Neue Use Cases ergänzen
bzw. bestehende Use Cases versioniert aktualisieren.

---

## 2. Interview starten

Wenn der Benutzer einen neuen Use Case erstellen möchte, zuerst fragen:

**A – Grundidee**

1. Was möchtest du erreichen?
2. Welches Problem soll gelöst werden?
3. Wer soll die Funktion benutzen?
4. Was soll der Benutzer konkret machen können?
5. Was soll am Ende als Ergebnis herauskommen?

Die Fragen einfach und ohne unnötige Fachbegriffe formulieren. Nicht alle
technischen Details vom Benutzer verlangen.

---

## 3. Ablauf abfragen

Anschließend den normalen Ablauf ermitteln:

1. Wie startet der Benutzer die Funktion?
2. Was macht der Benutzer zuerst?
3. Was passiert danach?
4. Welche Eingaben sind erforderlich?
5. Welche Entscheidungen kann der Benutzer treffen?
6. Welche Aktionen führt das Programm automatisch aus?
7. Was sieht der Benutzer währenddessen?
8. Wann ist der Vorgang erfolgreich abgeschlossen?

Wenn Antworten fehlen, gezielt nachfragen.

---

## 4. Daten und Dateien

Falls relevant, zusätzlich fragen:

- Welche Dateien werden verwendet?
- Woher kommen die Daten?
- Wo liegen die Dateien?
- Welche Dateiformate gibt es?
- Müssen Daten importiert werden?
- Müssen Daten exportiert werden?
- Soll der Benutzer Ordner auswählen können?
- Müssen Originaldateien erhalten bleiben?
- Soll automatisch ein Backup erstellt werden?

Nur Fragen stellen, die für den jeweiligen Use Case tatsächlich relevant sind.

---

## 5. Benutzeroberfläche

Falls eine Benutzeroberfläche benötigt wird, fragen:

- Was soll auf dem Bildschirm sichtbar sein?
- Welche Buttons werden benötigt?
- Welche Informationen sollen angezeigt werden?
- Wird eine Vorschau benötigt?
- Soll Drag-and-drop möglich sein?
- Soll es Fortschrittsanzeigen geben?
- Welche Einstellungen soll der Benutzer verändern können?

Claude darf anschließend selbst sinnvolle UI-Vorschläge ergänzen.

---

## 6. Automatisierung

Ermitteln:

- Was soll automatisch passieren?
- Was muss der Benutzer bestätigen?
- Welche Aktionen dürfen niemals automatisch ausgeführt werden?
- Soll das Programm Entscheidungen selbst treffen?
- Soll KI verwendet werden?
- Soll das Programm aus vorherigen Aktionen lernen?
- Müssen Aufgaben im Hintergrund laufen?

---

## 7. Fehler und Sonderfälle

Gezielt nach wichtigen Sonderfällen fragen:

- Was passiert bei fehlerhaften Daten?
- Was passiert, wenn Dateien fehlen?
- Was passiert bei einem Programmabsturz?
- Was passiert bei einem Neustart?
- Soll ein abgebrochener Vorgang fortgesetzt werden?
- Können Änderungen rückgängig gemacht werden?
- Welche Daten dürfen auf keinen Fall verloren gehen?

Claude soll zusätzlich selbst mögliche Edge Cases erkennen.

---

## 8. Priorität

Für jeden Use Case bestimmen:

- **MUSS** – Ohne diese Funktion ist der Use Case nicht sinnvoll nutzbar.
- **SOLL** – Wichtig, aber nicht zwingend für die erste Version.
- **KANN** – Komfort- oder Erweiterungsfunktion.

Wenn der Benutzer keine Priorität angibt, soll Claude anhand des Use Cases
einen Vorschlag machen.

---

## 9. Intelligente Nachfragen

Claude soll nicht starr einen Fragebogen abarbeiten.

- Die nächste Frage muss sich aus den vorherigen Antworten ergeben.
- Bereits beantwortete Informationen nicht erneut abfragen.
- Offensichtliche technische Details darf Claude selbst sinnvoll ergänzen.
- Bei wichtigen Annahmen muss Claude diese deutlich kennzeichnen.

Beispiel:

> Annahme: Die Originaldateien werden niemals verändert. Bearbeitungen
> erfolgen ausschließlich auf Kopien.

Der Benutzer kann solche Annahmen anschließend bestätigen oder korrigieren.

---

## 10. Use Case erstellen

Nach ausreichenden Informationen automatisch einen professionellen Use Case
erzeugen, im folgenden Format (in `USE_CASES.md`):

```
## UC-001 – [Name]

### Ziel
Beschreibung des gewünschten Ergebnisses.

### Benutzer
Wer verwendet die Funktion?

### Ausgangssituation
Welche Voraussetzungen bestehen?

### Auslöser
Was startet den Vorgang?

### Normaler Ablauf
1. Benutzer führt Aktion aus.
2. System reagiert.
3. Benutzer trifft gegebenenfalls Auswahl.
4. System verarbeitet Daten.
5. Ergebnis wird angezeigt bzw. gespeichert.

### Ergebnis
Was wurde erfolgreich erreicht?

### Alternative Abläufe
Andere mögliche Abläufe.

### Fehlerfälle
Mögliche Fehler und gewünschte Reaktionen.

### Anforderungen
Konkrete funktionale Anforderungen.

### Nichtfunktionale Anforderungen
Z. B. Geschwindigkeit, Datensicherheit, Bedienbarkeit, Offlinefähigkeit,
Stabilität, Wiederherstellbarkeit.

### Akzeptanzkriterien
Klare und testbare Bedingungen, wann der Use Case als fertig gilt.

### Priorität
MUSS / SOLL / KANN

### Abhängigkeiten
Andere Funktionen, Use Cases oder externe Systeme.

### Offene Punkte
Noch ungeklärte Fragen.
```

---

## 11. Automatisch technische Aufgaben ableiten

Nach Erstellung des Use Cases analysiert Claude selbstständig:

- Welche Komponenten müssen entwickelt werden?
- Welche bestehenden Komponenten werden verändert?
- Welche Dateien sind betroffen?
- Welche Bibliotheken werden benötigt?
- Welche Schnittstellen werden benötigt?
- Welche Tests müssen erstellt werden?
- Welche Risiken bestehen?
- Welche bestehenden Funktionen könnten betroffen sein?

Diese Informationen nicht ungeprüft erfinden. Zuerst vorhandenen
Projektcode und Projektdokumentation analysieren.

---

## 12. Claude-Code-Prompt erzeugen

Aus jedem bestätigten Use Case automatisch einen vollständigen
Implementierungs-Prompt erzeugen und in `USE_CASE_PROMPTS.md` ablegen:

```
## IMPLEMENTIERUNG UC-001

### Ziel
Implementiere folgenden Use Case:
[Beschreibung]

### Bestehendes Projekt
Lies zuerst:
- CLAUDE.md
- PLAN.md
- PROGRESS.md
- TODO.md
- DECISIONS.md
- CHANGELOG.md
- NEXT_STEPS.md
- USE_CASES.md

Analysiere anschließend den bestehenden Code.

### Anforderungen
[automatisch aus Use Case übernehmen]

### Akzeptanzkriterien
[automatisch übernehmen]

### Sicherheitsregel
Bestehende funktionierende Funktionen dürfen nicht beschädigt werden.
Vor Änderungen prüfen, welche bestehenden Komponenten betroffen sind.

### Implementierung
1. Projekt analysieren.
2. Implementierungsplan erstellen.
3. Abhängigkeiten prüfen.
4. Änderungen durchführen.
5. Tests durchführen.
6. Fehler korrigieren.
7. Akzeptanzkriterien überprüfen.
8. Projektdokumentation aktualisieren.
9. Fortschritt sichern.
10. Nächste Schritte dokumentieren.
```

---

## 13. Verknüpfung mit Projektdokumentation

Nach Bestätigung eines Use Cases automatisch prüfen, ob folgende Dateien
angepasst werden müssen:

- PLAN.md
- PROGRESS.md
- TODO.md
- DECISIONS.md
- CHANGELOG.md
- NEXT_STEPS.md

Dabei keine bestehenden Informationen löschen.

---

## 14. Nummerierung

Use Cases fortlaufend nummerieren: `UC-001`, `UC-002`, `UC-003`, usw.

Untergeordnete Use Cases können verwendet werden: `UC-003.1`, `UC-003.2`.

---

## 15. Änderungen

Wenn der Benutzer später sagt: „Ändere Use Case 4.“, muss Claude:

1. `USE_CASES.md` lesen.
2. UC-004 identifizieren.
3. Benutzer nach der gewünschten Änderung fragen, falls diese nicht eindeutig ist.
4. Auswirkungen auf andere Use Cases analysieren.
5. Use Case aktualisieren.
6. Zugehörigen Prompt in `USE_CASE_PROMPTS.md` aktualisieren.
7. Projektdokumentation aktualisieren.
8. Änderung im `CHANGELOG.md` dokumentieren.

---

## 16. Wichtige Grundregel

Der Benutzer beschreibt hauptsächlich **WAS** er erreichen möchte.

Claude ermittelt daraus selbstständig **WIE** es technisch sinnvoll
umgesetzt werden kann.

Der Benutzer soll nicht gezwungen werden, technische Architektur,
Bibliotheken, Datenstrukturen oder Implementierungsdetails festzulegen,
wenn Claude diese anhand des vorhandenen Projekts selbst bestimmen kann.

Bei mehreren technisch sinnvollen Möglichkeiten soll Claude die beste
Variante empfehlen und nur dann nachfragen, wenn die Entscheidung
erhebliche Auswirkungen auf Funktion, Kosten, Datenschutz oder Bedienung
hat.

---

## 17. Startbefehle

- **„Neuer Use Case“** → Claude startet automatisch das Use-Case-Interview
  (Abschnitt 2).
- **„Use Cases anzeigen“** → Claude liest `USE_CASES.md` und zeigt eine
  strukturierte Übersicht.
- **„Use Case umsetzen UC-XXX“** → Claude liest den entsprechenden Use Case
  und den zugehörigen Prompt aus `USE_CASE_PROMPTS.md`, analysiert den
  aktuellen Projektstand und beginnt anschließend mit der Umsetzung.
- **„Use Cases prüfen“** → Claude analysiert alle vorhandenen Use Cases auf:
  - Widersprüche
  - Überschneidungen
  - fehlende Anforderungen
  - fehlende Fehlerfälle
  - Abhängigkeiten
  - nicht testbare Akzeptanzkriterien
  - mögliche neue Use Cases

---

## 18. Selbstständige Verbesserung

Claude soll aus den Antworten des Benutzers selbst weitere sinnvolle
Anforderungen erkennen.

Beispiel — Benutzer: „Ich möchte Videos per Drag-and-drop hineinziehen.“

Claude kann daraus unter anderem ableiten:

- Drag-and-drop-Zone erforderlich
- unterstützte Videoformate definieren
- ungültige Dateien erkennen
- mehrere Dateien berücksichtigen
- Importfortschritt anzeigen
- Fehler beim Import verständlich anzeigen

Solche Punkte werden als **abgeleitete Anforderungen** gekennzeichnet.

Claude soll damit aus einer einfachen Idee einen technisch vollständigen
und testbaren Use Case entwickeln, ohne dass der Benutzer jedes Detail
selbst formulieren muss.
