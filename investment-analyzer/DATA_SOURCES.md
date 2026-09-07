# Quellen- und Lizenzmatrix (Milestone 0)

Dokumentierter Quellenkatalog gemäß Auftrag §3. Kein Anspruch auf
Vollständigkeit „des Internets" — nur die hier gelisteten, geprüften
Quellen werden angebunden. Jede Zeile ist ein Kandidat für einen
`connectors`-Adapter (Auftrag §4); die tatsächliche Umsetzungsreihenfolge
folgt der Kostenvariante, die der Nutzer für den Start wählt (siehe
`MILESTONE_0.md`, Frage B1–B2).

Stand der Angaben: **2026-09-07**, auf Basis öffentlich bekannter
Preismodelle/AGB der Anbieter. Preise und Limits ändern sich häufig —
vor produktivem Einsatz jeder Quelle sind AGB/Preisliste erneut zu
prüfen und das Ergebnis in dieser Datei mit Datum zu vermerken
(„Zuletzt geprüft: …").

## Quellenhierarchie gemäß Auftrag §3 (Stufe 1 = höchste Priorität)

### Stufe 1 — Börsenaufsichten und Originalmeldungen

| Quelle | Abdeckung | Kostenvariante | Kosten (ca.) | Lizenz / Nutzungsbedingungen | Rate Limits | Empfehlung |
|---|---|---|---|---|---|---|
| SEC EDGAR (submissions API, XBRL frames, Full-Text-Search) | USA, alle SEC-registrierten Emittenten | kostenlos | 0 € | Public Domain (US-Regierungswerk); Pflicht: aussagekräftiger `User-Agent`-Header mit Kontaktadresse | Fair-Access-Policy, empfohlen ≤ 10 req/s | **Primärquelle Milestone 2 (USA)** |
| Unternehmensregister/Bundesanzeiger (DE, Jahresabschlüsse) | Deutschland | kostenlos (Einsicht) / kostenpflichtig (Volltext-Bulk) | 0 € Einzelabruf; Bulk auf Anfrage | Nutzungsbedingungen Bundesanzeiger beachten; kein systematisches Scraping ohne Prüfung der AGB | unbekannt, konservativ drosseln | Milestone 2+ (EU-Erweiterung) |
| Ad-hoc-/Regulatory-News (EQS Group DGAP, national) | DE/EU | teils kostenlos (RSS aktuelle Meldungen), Historie kostenpflichtig | 0 € RSS; Archiv-API auf Anfrage | Redistribution meist eingeschränkt, nur Einzelabruf/Verlinkung prüfen | RSS unlimitiert (Fair Use) | Milestone 2+ (EU-Erweiterung) |
| ESMA / nationale Aufsichtsbehörden (Register, z. B. BaFin) | EU | kostenlos | 0 € | öffentliche Register, Nutzung im Rahmen der jeweiligen AGB | quellenabhängig | Milestone 2+ |

### Stufe 2 — Geschäftsberichte, IR-Seiten, Präsentationen

| Quelle | Abdeckung | Kostenvariante | Kosten | Lizenz | Rate Limits | Empfehlung |
|---|---|---|---|---|---|---|
| Unternehmens-IR-Websites (PDF-Berichte, Präsentationen) | global | kostenlos | 0 € | öffentlich zugänglich, aber urheberrechtlich geschützt → nur Zitat/Verweis, kein Volltext-Republishing; `robots.txt` je Domain beachten | pro Domain individuell, konservativ (z. B. 1 req/s) | Milestone 2/3 (Ergänzung) |
| IR-RSS-Feeds (soweit angeboten) | global, uneinheitlich | kostenlos | 0 € | öffentlich | Fair Use | Milestone 2/3 |

### Stufe 3 — Börsen-/Fundamentaldatenanbieter (lizenziert)

| Quelle | Abdeckung | Kostenvariante | Kosten (ca./Monat) | Lizenz | Rate Limits | Empfehlung |
|---|---|---|---|---|---|---|
| Alpha Vantage (Free Tier) | global, Kurse + einfache Fundamentaldaten | kostenlos | 0 € | offizielle API, Nutzung gemäß ToS, kein Redistribution-Verbot für Eigenanwendung | 5 req/min, 25–500 req/Tag (Free) | **Marktdaten-Primärquelle Milestone 2 (Kostenlos-Paket)** |
| Stooq (CSV-Export) | global, historische Kurse | kostenlos | 0 € | inoffiziell, ToS unklar/nicht vertraglich abgesichert | unbekannt | nur als Fallback/Test, nicht produktiv ohne Klärung |
| Yahoo-Finance-Endpunkte (inoffiziell) | global | kostenlos, aber **nicht ToS-konform** (Scraping durch Yahoo-AGB untersagt) | 0 € | **nicht empfohlen** — Auftrag §3 verbietet Umgehen von Schutzmaßnahmen | — | **ausgeschlossen** |
| Financial Modeling Prep | global, Fundamentaldaten + Kurse + Estimates | günstig | ca. 15–50 $ (Starter/Premium) | kommerzielle API-Lizenz, Redistribution je Tarif geregelt | tarifabhängig, deutlich höher als Free-APIs | Kandidat für „günstig"-Paket |
| EOD Historical Data | global, Fundamentaldaten + Kurse | günstig | ca. 20–80 $ | kommerzielle API-Lizenz | tarifabhängig | Kandidat für „günstig"-Paket |
| Twelve Data | global, Kurse + Fundamentaldaten | günstig | ca. 30–80 $ | kommerzielle API-Lizenz | tarifabhängig | Alternative zu FMP/EODHD |
| Polygon.io | primär USA, gute Echtzeitnähe | günstig–professionell | ca. 29–199 $ | kommerzielle API-Lizenz | tarifabhängig | Option falls Fokus USA |
| Refinitiv Workspace/Eikon, Bloomberg Terminal/B-PIPE, FactSet, S&P Capital IQ | global, institutioneller Standard | professionell | mehrere Hundert bis mehrere Tausend €/Monat, meist Jahresverträge | strenge Enterprise-Lizenzen, Redistribution i. d. R. verboten | hoch, aber vertraglich geregelt | nur bei ausdrücklichem Bedarf/Budget |

### Stufe 4 — Zentralbanken und Statistikämter

| Quelle | Abdeckung | Kostenvariante | Kosten | Lizenz | Rate Limits | Empfehlung |
|---|---|---|---|---|---|---|
| EZB Statistical Data Warehouse (SDW) API | Eurozone, Makrodaten | kostenlos | 0 € | offene Datenlizenz (Reuse erlaubt, Quellenangabe) | keine strengen Limits bekannt | **Makro-Primärquelle** |
| Weltbank Open Data API | global, Makrodaten | kostenlos | 0 € | CC-BY 4.0 | großzügig | **Makro-Primärquelle** |
| Destatis (Statistisches Bundesamt) | Deutschland | kostenlos | 0 € | Datenlizenz Deutschland (Namensnennung) | großzügig | Ergänzung DE |
| FRED (St. Louis Fed) | USA + international aggregiert | kostenlos | 0 € | offene API, Quellenangabe | großzügig | Ergänzung Makro USA |

### Stufe 5/6 — Unternehmensmeldungen, Nachrichten, aggregierte Suche

| Quelle | Abdeckung | Kostenvariante | Kosten | Lizenz | Rate Limits | Empfehlung |
|---|---|---|---|---|---|---|
| GDELT Project (API/BigQuery) | global, Nachrichtenereignisse | kostenlos | 0 € | öffentlich, akademisch/frei nutzbar mit Attribution | großzügig, aber Volumen beachten | **Nachrichten-Primärquelle Milestone 5** |
| NewsAPI.org | global | kostenlos (Dev, stark limitiert) / günstig (Business) | 0 € Dev; ab ca. 449 $ Business (nur Volltext-Kommerz) | Dev-Tarif nur für Entwicklung, nicht produktiv | 100 req/Tag (Dev) | Milestone 5, Dev-Tarif nur zum Testen |
| Unternehmens-Pressemitteilungen (eigene RSS/PR-Seiten) | global | kostenlos | 0 € | öffentlich | Fair Use | Milestone 5 |
| Qualitätsmedien (Reuters, dpa-AFX u. a.) direkt | global/DE | überwiegend kostenpflichtig (Lizenzfeed) | variabel, oft vierstellig/Monat | strenge Lizenzverträge | vertraglich | nur bei Bedarf, nicht für Kostenlos-/Günstig-Paket vorgesehen |

### Stufe 7 — Analystenschätzungen (nur Zusatzsignal, Auftrag §3)

| Quelle | Abdeckung | Kostenvariante | Kosten | Lizenz | Empfehlung |
|---|---|---|---|---|---|
| Visible Alpha, Refinitiv I/B/E/S | global | professionell | hoch | Enterprise-Lizenz | nur bei Bedarf |
| Estimates-Felder in FMP/EODHD (limitiert) | global, eingeschränkt | günstig | in Basistarif teilweise enthalten | kommerzielle API-Lizenz | pragmatische Alternative für „günstig"-Paket |

## Kostenvarianten im Überblick

### Paket „Kostenlos" (0 €/Monat)

SEC EDGAR + EZB SDW + Weltbank + Destatis/FRED + GDELT + Alpha Vantage
Free + Unternehmens-IR-Seiten/RSS.

- **Stärken:** guter Start für USA (EDGAR sehr strukturiert), solide
  Makrodaten, kostenlose Nachrichtenbasis (GDELT).
- **Schwächen:** EU/DE-Fundamentaldaten strukturiert schlechter
  abgedeckt (Bundesanzeiger schwer automatisiert, Ad-hoc-Historie meist
  kostenpflichtig); Alpha-Vantage-Free-Limits (5 req/min) bremsen große
  Screener-Läufe erheblich; keine Analystenschätzungen.
- **Empfehlung:** guter Startpunkt für Milestone 1–2, um Architektur und
  Provenienz-Handling zu bauen und zu testen, bevor Geld investiert wird.

### Paket „Günstig" (ca. 50–150 €/Monat)

Kostenlos-Paket + ein Fundamentaldatenanbieter (Financial Modeling Prep
oder EOD Historical Data oder Twelve Data) für breitere globale
Abdeckung und höhere Rate Limits.

- **Stärken:** deutlich bessere Europa-/Global-Abdeckung, brauchbare
  Analystenschätzungen als Zusatzsignal, praktikable Rate Limits für
  einen persönlichen Screener.
- **Schwächen:** weiterhin keine Institutionsqualität bei Tiefe/Historie;
  einzelne Anbieterausfälle möglich (Single-Vendor-Risiko).
- **Empfehlung:** realistischer Zielzustand für einen Privatnutzer mit
  ernsthaftem Anspruch.

### Paket „Professionell" (mehrere Hundert bis mehrere Tausend €/Monat)

Refinitiv/Bloomberg/FactSet + Visible Alpha o. Ä.

- **Stärken:** Institutionsqualität, tiefe Historie, umfassende
  Analystenkonsens-Daten.
- **Schwächen:** für einen Einzelnutzer i. d. R. unverhältnismäßig teuer,
  oft nur mit Jahresverträgen/Mindestabnahmen erhältlich.
- **Empfehlung:** nur falls Nutzer das Budget ausdrücklich bereitstellt.

## Grundsätze für jeden Connector (Auftrag §4, gilt ab Milestone 2)

- Timeout, Retry mit Backoff, Rate Limiting, Cache, Datenvalidierung,
  Fehlerprotokoll, Lizenzhinweis — pro Connector Pflichtbestandteile.
- `robots.txt`, ToS, Urheberrecht, Rate Limits, Paywalls respektieren;
  keine Schutzmaßnahmen umgehen (Auftrag §3, §12).
- Fällt eine Quelle aus: klarer Fehler statt eines unbemerkt veralteten
  Werts (Auftrag §4).
- URL-Allowlist pro Connector, SSRF-Schutz (Auftrag §12, siehe
  `SECURITY.md`).

## Entscheidung (2026-09-07, siehe `MILESTONE_0.md` und ADR-8/ADR-9)

- **Start-Kostenvariante: Kostenlos.**
- **Marktauswahl: breit** (USA, Deutschland, übriges Europa, weitere
  global offen) — keine initiale Einschränkung.
- **Milestone-2-Connectoren:** SEC EDGAR (Meldungen, Primärquelle) +
  Alpha Vantage Free (Marktdaten). Bekannte Lücke: keine gleichwertige
  kostenlose, strukturierte Meldungs-Primärquelle für DE/EU — wird im
  UI als geringere Datenabdeckung/Konfidenz für EU-Werte ausgewiesen,
  nicht verschwiegen. Upgrade auf „günstig" bleibt bei Bedarf möglich.

## Weiterhin offen

- Ob bereits eigene API-Schlüssel/Verträge existieren (z. B. FMP/EODHD),
  die die obige Auswahl später ändern würden.
