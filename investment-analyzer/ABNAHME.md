# Abnahme-Checkliste — Investment-Analysator (Auftrag §15)

Ehrliche, kriterienweise Bewertung gegen die neun Abnahmekriterien aus
`AUFTRAG.md` §15, ursprünglich Stand Milestone 8 (2026-09-08),
aktualisiert nach dem Bau der Unternehmensdetail-Seite (2026-09-09,
siehe ADR-27) — Kriterium 8 dadurch neu bewertet. Jedes Kriterium wird
als **erfüllt**, **teilweise erfüllt** oder **nicht erfüllt**
eingestuft — mit Begründung. Ziel ist Ehrlichkeit über den
tatsächlichen Stand, nicht eine geschönte Abnahme (Auftrag §11/§16).

## Zusammenfassung

| # | Kriterium | Status |
| --- | --- | --- |
| 1 | Kompletter Lauf reproduzierbar | Teilweise erfüllt |
| 2 | Keine unbelegte Kennzahl im Bericht | Erfüllt (strukturell, an Syntheticdaten geprüft) |
| 3 | Datenalter/Marktdatenverzögerung sichtbar | Erfüllt |
| 4 | Klarer Fehler statt erfundener Analyse bei Quellenausfall | Erfüllt |
| 5 | ≥30 Unit-/Integrationstests + zentrale End-to-End-Tests | Erfüllt (504 Tests) |
| 6 | DCF/Kernkennzahlen gegen Handrechnungen geprüft | Teilweise erfüllt |
| 7 | Backtests nachweislich ohne Look-ahead | Erfüllt (echter Fund der unabhängigen Prüfung noch in dieser Runde behoben) |
| 8 | Exporte = Oberflächenwerte | Erfüllt |
| 9 | Unabhängiger Security-/Plausibilitätscheck dokumentiert | Erfüllt (fand einen echten, behobenen Fehler) |

**Gesamturteil:** Das Programm ist **noch nicht vollständig
abnahmefähig** im strengen Sinn von Auftrag §15 — ein Kriterium (1) ist
strukturell/technisch fundiert, aber empirisch nicht vollständig
nachweisbar, und ein Kriterium (6) bleibt an echten Unternehmensdaten
offen. Beide verbleibenden Lücken haben dieselbe, bereits seit
Milestone 2 durchgängig dokumentierte Ursache: kein Internetzugang in
dieser Entwicklungs-Sandbox (siehe `PROGRESS.md`). Kriterium 8 galt bei
der ursprünglichen Milestone-8-Abnahme noch als nicht erfüllt (fehlende
UI-Detailseite) — mit der seither gebauten Unternehmensdetail-Seite
(ADR-27) gilt es jetzt als erfüllt. Das ist eine bewusste, durchgängig
dokumentierte Grenze dieser Entwicklungsumgebung, kein verschwiegener
Mangel.

Kriterium 7 verdient eine besondere Erwähnung: Die unabhängige Prüfung
(Kriterium 9) fand hier einen ECHTEN, für die Abnahme blockierenden
Fehler — einen Look-ahead-Bias in den Warnsignal-Checks, der von der
ursprünglichen Selbsteinschätzung des eigenen Reviews übersehen worden
war. Der Fehler wurde noch innerhalb dieser Milestone-8-Runde behoben
und mit gezielten Regressionstests abgesichert (siehe `DECISIONS.md`
ADR-25). Das ist kein Grund, das Kriterium als „nicht erfüllt"
einzustufen (der Code ist jetzt tatsächlich korrekt), aber ein
wichtiger Beleg dafür, dass die unabhängige Prüfung in diesem Projekt
keine Formsache war, sondern einen Unterschied gemacht hat.

## Kriterium 1 — „ein kompletter Lauf reproduzierbar ist"

**Teilweise erfüllt.**

Die gesamte deterministische Pipeline (Connector → Ingestion →
Fundamentaldaten → Bewertung → Score → Nachrichten → Portfolio →
Backtest → Export) ist vollständig implementiert; jede Stufe ist bei
gleichem Datenbankstand und gleichem `as_of`-Stichtag nachweislich
reproduzierbar (Grundvoraussetzung für Point-in-time-Korrektheit,
ADR-6, durchgängig getestet).

**Offen:** Seit dem Marktscreener (Auftrag §10 Seite 2, siehe ADR-26)
und der Unternehmensdetail-Seite (Auftrag §10 Seite 4, siehe ADR-27)
existiert jetzt in der Oberfläche der komplette Weg von einem realen
Datenabruf (SEC EDGAR, optional Alpha Vantage) bis zum fertigen Bericht
(Kennzahlen, Bewertung, Score, JSON-/Excel-/PDF-Export) — mit
synthetisch befüllter Testdatenbank per Playwright end-to-end
verifiziert (siehe `PROGRESS.md`). Offen bleibt allein: ein kompletter
Lauf gegen die **echten** externen Datenquellen (SEC EDGAR, Alpha
Vantage, GDELT, IR-RSS) wurde in dieser Entwicklungsumgebung **kein
einziges Mal tatsächlich ausgeführt**, weil ausgehender Internetzugriff
hier durch die Sandbox-Egress-Policy blockiert ist (verifiziert per
`curl`, siehe `PROGRESS.md` seit Milestone 2). Reproduzierbarkeit ist
bislang nur mit synthetischen Testdaten nachgewiesen, nicht mit einem
echten Lauf gegen reale Marktdaten.

## Kriterium 2 — „keine unbelegte Kennzahl im Bericht erscheint"

**Erfüllt (strukturell), mit Einschränkung.**

Das Provenienz-first-Datenmodell (`normalization.DataPoint`, ADR-6)
erzwingt dies architektonisch: jeder im `ReportBundle` gezeigte Wert
stammt entweder aus einem gespeicherten `DataPoint` mit
`document_url`/`content_hash`, oder ist als Annahme ausdrücklich
gekennzeichnet (`ReportBundle.assumptions`,
`ValuationReport.missing_data_notes`,
`FundamentalsReport.missing_fields`). Kein Platzhalterwert, der wie
eine echte Zahl aussieht, existiert im Code — durchgängig getestet
(u. a. `test_fundamentals_report_firma_b_datenluecken_und_warnsignal`,
`test_build_report_bundle_ohne_jegliche_daten`).

**Einschränkung:** wie bei Kriterium 1 — nur an synthetischen Daten
geprüft, nicht an einem echten Lauf mit echten Quellen.

## Kriterium 3 — „Datenalter und Marktdatenverzögerung sichtbar sind"

**Erfüllt.** `ReportHeader.as_of`/`generated_at_utc`/
`market_data_delay_note` (letzteres eine ehrliche feste Formulierung,
da kein Streaming-Feed existiert — die tatsächliche Verzögerung ist
unbekannt und wird nicht vorgetäuscht); UI-Seite „Start/Datenstatus"
zeigt Analysezeit und denselben Hinweis.

## Kriterium 4 — „bei Quellenausfall ein klarer Fehler statt einer erfundenen Analyse"

**Erfüllt.** `ConnectorError`-Hierarchie (`ConnectorHTTPError`,
`ConnectorTimeoutError`, `ConnectorRateLimitedError`,
`ConnectorValidationError`) wird bei jedem Fehlschlag geworfen; es gibt
KEINEN stillschweigenden Rückfall auf einen abgelaufenen Cache-Eintrag
oder eine erfundene Zahl. Durchgängig getestet
(`tests/connectors/test_base_connector.py`, u. a.
`test_erschoepfte_retries_werfen_letzten_fehler`,
`test_uebergrosse_antwort_wird_ohne_retry_abgelehnt`). Die UI zeigt bei
fehlender Migration/fehlenden Daten ebenfalls einen expliziten Hinweis
statt einer Platzhalterzahl.

## Kriterium 5 — „mindestens 30 Unit-/Integrationstests und zentrale End-to-End-Tests"

**Erfüllt, deutlich übertroffen.** 453 automatisierte Tests (Stand
2026-09-08), `ruff check .` und `mypy src` beide fehlerfrei. Zentrale
End-to-End-Tests vorhanden: `score_entity` gegen echte Datenbank
(`tests/scoring/test_score.py`), vollständiger `ReportBundle`-Aufbau
inkl. JSON-/Excel-/PDF-Export, Backtest-Engine gegen Datenbank inkl.
Look-ahead-Nachweis, echter Alembic-Migrationszyklus per Subprozess
(`tests/db/test_schema.py::test_alembic_migration_gegen_sqlite`),
end-to-end getesteter Restore-Prozess (`tests/db/test_backup.py`).

## Kriterium 6 — „DCF und Kernkennzahlen gegen Handrechnungen geprüft"

**Teilweise erfüllt.**

Umfangreiche, präzise von Hand nachgerechnete synthetische Testfälle
für DCF (`tests/valuation/test_dcf.py`), Multiples
(`tests/valuation/test_multiples.py`), Wachstumsraten/Margen/Renditen
(`tests/fundamentals/test_calculations.py`,
`tests/fundamentals/test_report.py`) — jeder Testfall ist so
konstruiert, dass das erwartete Ergebnis unabhängig von Hand
nachrechenbar ist (siehe Docstrings dieser Testdateien), und die
Berechnungscode-Korrektheit für diese Eingaben ist damit bewiesen.

**Offen:** Eine Verifikation an **echten, veröffentlichten
Geschäftszahlen** (mind. drei reale Unternehmen, wie im Auftrag
vorgesehen) konnte in dieser Sandbox mangels Internetzugang nicht
durchgeführt werden — dieselbe, seit Milestone 2/3/4 durchgängig
dokumentierte Einschränkung (siehe `PROGRESS.md`/`NEXT_STEPS.md`).

## Kriterium 7 — „Backtests nachweislich kein Look-ahead"

**Erfüllt — nach Behebung eines von der unabhängigen Prüfung (Kriterium
9) gefundenen, echten Verstoßes.**

Ursprünglicher Nachweis (ADR-22): Universums-Ebene
(`tests/backtesting/test_universe.py`) und vollständiger Backtest-Lauf
(`tests/backtesting/test_engine.py::
test_spaeter_bekannt_gewordener_kandidat_veraendert_frueheres_
backtest_ergebnis_nicht`) zeigen bit-identische Ergebnisse vor/nach
Eintreffen eines erst später bekannt gewordenen Kandidaten. Jede
Abfrage in der Kernpipeline filtert konsequent über
`retrieved_at_utc <= as_of` (ADR-6).

**Aber:** Die unabhängige Prüfung fand eine reale Lücke, die dieser
Nachweis nicht abdeckte: `risk/warning_signals.py::run_all_checks`
nahm kein `as_of` entgegen und griff dadurch auf den AKTUELLEN
Zeitpunkt statt den Analysestichtag zurück — ein Warnsignal (und damit
der davon abhängige `total_score`, das Ranking-Kriterium von
`select_top_n`) konnte von Daten beeinflusst werden, die zum
Backtest-Stichtag noch gar nicht bekannt waren. Der bestehende Test
deckte dieses Szenario nicht ab (er testet eine neue Entity, nicht eine
später eintreffende Zeile für eine bereits bekannte Entity). **Noch in
dieser Milestone-8-Runde behoben** (ADR-25) — `as_of` wird jetzt durch
jeden Warnsignal-Check gereicht, zwei neue Regressionstests
(`tests/risk/test_warning_signals.py::
test_run_all_checks_ignoriert_zum_stichtag_noch_unbekannte_daten`,
`tests/scoring/test_score.py::
test_score_entity_ignoriert_zum_stichtag_noch_unbekanntes_
warnsignal`) beweisen exakt das vom Review benannte Szenario. Ohne
diese Behebung wäre dieses Kriterium NICHT erfüllt gewesen — die
ursprüngliche Selbsteinschätzung „erfüllt" war zu diesem Zeitpunkt
sachlich falsch, korrigiert durch die unabhängige Prüfung.

## Kriterium 8 — „Exporte dieselben Werte wie die Oberfläche"

**Erfüllt.**

Strukturell abgesichert: `ReportBundle` (ADR-21) ist die EINZIGE
Datenquelle für JSON-, Excel- und PDF-Export — die drei Formate können
nicht voneinander abweichen, da sie exakt dieselbe
`report_bundle_to_dict()`-Struktur lesen (getestet u. a. in
`tests/reports/test_excel_export.py::
test_zusammenfassung_zeigt_dieselben_werte_wie_json_export`).

Seit der neuen Seite „Unternehmensdetail mit Quellenleiste" (Auftrag
§10, Seite 4, siehe ADR-27) gibt es jetzt auch eine UI-Seite, die
Berichtswerte tatsächlich anzeigt — `ui/detail.py` rendert
AUSSCHLIESSLICH aus demselben `report_bundle_to_dict()`-Dict wie die
Exportformate, berechnet selbst nichts nach (Auftrag §11). Damit gilt
dieselbe strukturelle Garantie, die bislang nur zwischen den drei
Exportformaten galt, jetzt auch für die Oberfläche: Anzeige und Export
lesen denselben Speicherwert, können also nicht auseinanderlaufen. Die
drei Download-Buttons auf der Detailseite bauen zudem aus genau dem
bereits im Speicher vorliegenden `bundle`-Objekt, nicht aus einer
zweiten, separaten Berechnung.

Mit echtem Playwright-Browser gegen eine synthetisch befüllte
Testdatenbank verifiziert: alle auf der Detailseite angezeigten Werte
(Kennzahlen, Bewertung inkl. DCF-Szenarien, Score) sind exakt dieselben
Werte wie im `ReportBundle`, aus dem auch die Exporte gebaut werden
(siehe `PROGRESS.md`). Ein Vergleich mit **echten**, über SEC EDGAR
abgerufenen Daten steht weiterhin aus (siehe Kriterium 1) — das ändert
nichts an der hier bewerteten strukturellen Garantie, die unabhängig
vom Dateninhalt gilt.

## Kriterium 9 — „unabhängiger Security- und Plausibilitätscheck dokumentiert"

**Erfüllt — mit einer wichtigen Einschränkung, die hier transparent
gemacht wird statt verschwiegen zu werden.**

Zwei Prüfschritte wurden durchgeführt:

1. **Eigener, selbst durchgeführter Review** (ADR-23, ADR-24): der
   Agent, der den Code geschrieben hat, hat systematisch jede
   Behauptung in `SECURITY.md` gegen das tatsächliche Codeverhalten
   geprüft und mehrere echte Lücken gefunden und behoben
   (Downloadgrößen-Begrenzung, unvollständige Log-Redaction, fehlender
   Pflichthinweis in Exporten, XML-Entity-Expansion im IR-RSS-
   Connector). Dieser Review ist gründlich, aber **nicht unabhängig**
   im eigentlichen Sinn — derselbe Akteur, der den Code baute, kann
   dieselben blinden Flecken haben.
2. **Separater, unabhängiger Review-Durchlauf:** Ein zweiter,
   eigenständiger Agentenlauf ohne Kenntnis der vorherigen
   Implementierungsentscheidungen wurde beauftragt, denselben
   Codestand mit frischem Blick gegen `SECURITY.md`, `METHODOLOGY.md`
   und die Backtesting-Look-ahead-Garantie zu prüfen — genau die in
   `PLAN.md` (Milestone 8, Rollen `security-reviewer`/`test-agent`)
   vorgesehene Rollentrennung, auch wenn hier durch zwei
   Agentendurchläufe statt formal getrennter Rollen umgesetzt. Dieser
   Review war kein Alibi-Durchlauf: er fand einen ECHTEN, blockierenden
   Fehler (Look-ahead-Bias in den Warnsignal-Checks, siehe Kriterium 7),
   der die Selbsteinschätzung des eigenen Reviews (ADR-23/24) widerlegt
   hätte, sowie zwei weitere reale Härtungspunkte (Downloadgrößen-
   Prüfung erst nach vollständiger Pufferung, HTML-Sanitizing-Fallback
   ohne Markup-Entfernung) und eine ehrlich zu dokumentierende, bewusst
   nicht behobene Restlücke (SSRF-Time-of-check-to-time-of-use). Alle
   vier Befunde sind in `DECISIONS.md` ADR-25 dokumentiert; die ersten
   drei wurden noch in dieser Milestone-8-Runde behoben und getestet,
   der vierte als tragbares Restrisiko mit Begründung festgehalten.

Diese zweistufige Vorgehensweise erfüllt das Kriterium in der Sache —
eine zweite, vom ursprünglichen Code unabhängige Prüfinstanz hat
tatsächlich stattgefunden UND einen für die Abnahme relevanten Fehler
gefunden, der sonst unentdeckt geblieben wäre. Kein menschlicher
externer Prüfer war im Rahmen dieses Projekts vorgesehen
(vollständige Umsetzung durch Claude Code, Auftrag §4).
