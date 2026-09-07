# Milestone 0 — Klärung und Datenlizenzen

Zusammenfassung der Milestone-0-Lieferobjekte gemäß Auftrag §16. Dies
ist die zentrale Übersicht; Details stehen in den verlinkten Dokumenten.

- **Fragenliste:** siehe unten
- **Quellen-/Lizenzmatrix + Kostenvarianten:** `DATA_SOURCES.md`
- **Architekturentscheidung:** `DECISIONS.md` (ADR-1 bis ADR-6)
- **Verbindlicher Implementierungsplan:** `PLAN.md`

**Noch keine Produktivimplementierung**, solange die unten offenen
Fragen nicht beantwortet sind (Auftrag §14, Milestone 0). Milestone 1
beginnt erst nach Freigabe.

## Fragenliste

Die wichtigsten, Milestone-1/2-blockierenden Fragen wurden dem Nutzer
per Auswahlfrage direkt gestellt (siehe Antworten unten, sobald
vorliegend). Die übrigen Fragen betreffen Werte, die ohnehin beim
allerersten Programmstart über den in Auftrag §2 vorgesehenen
Ersteinrichtungsdialog abgefragt und jederzeit änderbar gespeichert
werden — hierfür werden unten sinnvolle Startwerte vorgeschlagen, die
der Nutzer bestätigen oder korrigieren kann.

### A. Blockierend für Milestone 1/2 (per Rückfrage gestellt)

1. **Projektstruktur:** Neues Unterverzeichnis `investment-analyzer/`
   in diesem bestehenden Repo (`nodotore/Testprojekt`), oder ein
   separates, neues Repository?
2. **Kostenvariante Datenquellen für den Start:** kostenlos / günstig
   (~50–150 €/Monat) / professionell / gemischt je Quelle? (siehe
   `DATA_SOURCES.md` für Details je Variante)
3. **Prioritäre Märkte/Börsen für Milestone 2:** welche sollen zuerst
   angebunden werden (USA, Deutschland, übriges Europa, weitere)?
4. **Deployment-Ziel Version 1:** rein lokal unter Windows mit SQLite
   (einfach, kein Docker nötig), oder Docker Compose mit PostgreSQL
   (produktionsnäher, benötigt Docker Desktop)?

### B. Ergänzend, mit vorgeschlagenem Standardwert (per Ersteinrichtungsdialog in der App, Auftrag §2)

Diese Punkte müssen laut Auftrag ohnehin beim ersten Programmstart als
änderbares Profil abgefragt werden. Vorschlag für sinnvolle
Standardwerte, sofern der Nutzer keine abweichende Präferenz nennt:

5. Ausschlussbranchen/-werte: standardmäßig keine, konfigurierbar.
6. Anlagehorizont: „mittelfristig" als Vorbelegung.
7. Risikoklasse: „ausgewogen" als Vorbelegung.
8. Bevorzugter Stil: „Mischung" (Value/Qualität/Wachstum/Dividende) als
   Vorbelegung.
9. Referenzwährung: EUR; Vergleichsindex abhängig von Antwort zu Frage 3
   (z. B. MSCI World bei globalem Fokus, DAX/MDAX bei DE-Fokus).
10. Mindest-/Höchstmarktkapitalisierung: Standard-Ausschluss von
    Microcaps/Pennystocks/illiquiden Werten gemäß Auftrag §2 (konkrete
    Schwellenwerte, z. B. Mindest-Marktkap. 1–2 Mrd. €/US-$, werden in
    Milestone 1 als konfigurierbarer Default vorgeschlagen und vom
    Nutzer im Ersteinrichtungsdialog bestätigt).
11. Maximale Positionsgröße und gewünschte Kandidatenzahl: Standard 10
    Kandidaten (passend zu Auftrag §8a „Top 10"), Positionsgröße als
    Bandbreite, kein fixer Wert.
12. Speicherort für Berichte/Exporte: Standard `%USERPROFILE%\InvestmentAnalyzer\reports`,
    änderbar im Ersteinrichtungsdialog.
13. Ausgabeformate: alle vier (Dashboard, PDF, Excel, JSON) werden von
    Anfang an gebaut, wie in Auftrag §2/§10 gefordert — keine
    Priorisierung nötig, da alle Pflicht sind.

### C. Weitere organisatorische Fragen

14. Existieren bereits eigene API-Zugänge/Lizenzen (z. B. Financial
    Modeling Prep, EODHD, NewsAPI Business), die in `DATA_SOURCES.md`
    berücksichtigt werden sollen?
15. Nutzerzahl: ausschließlich Einzelnutzer (kein Auth-/Multi-User-System
    in Version 1 nötig) — bitte bestätigen oder widersprechen.
16. Bestätigung des Haftungsausschlusses/Research-only-Charakters gemäß
    Auftrag §1/§12 (keine Kaufempfehlung, keine automatische Order).

## Antworten des Nutzers

*(wird nach Rückmeldung ausgefüllt und in `DECISIONS.md` als ADR-7ff.
festgehalten)*

| Frage | Antwort | Datum |
|---|---|---|
| 1 | offen | — |
| 2 | offen | — |
| 3 | offen | — |
| 4 | offen | — |
| 5–16 | offen / Standardwerte vorgeschlagen | — |
