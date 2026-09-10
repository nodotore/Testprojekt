from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from investment_analyzer.db import create_all_tables, create_db_engine, create_session_factory
from investment_analyzer.entity_resolution.models import IdentifierType
from investment_analyzer.entity_resolution.service import IdentifierSpec, find_or_create_entity
from investment_analyzer.portfolio.concentration import ConcentrationBreakdown
from investment_analyzer.portfolio.csv_import import import_watchlist_csv
from investment_analyzer.portfolio.risk_metrics import DrawdownResult
from investment_analyzer.ui.watchlist import (
    _drawdown_dataframe,
    _konzentration_dataframe,
    _list_watchlist,
)


def _session_factory(tmp_path: Path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'ui-watchlist-test.db'}")
    create_all_tables(engine)
    return create_session_factory(engine)


def test_list_watchlist_ohne_eintraege_ist_leer(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        assert _list_watchlist(session) == []


def test_list_watchlist_zeigt_unternehmensname_und_notiz(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    csv_text = "id_type,id_value,name,note\ncik,0000000001,Firma E,Beobachten wegen Kursrückgang\n"

    with session_factory() as session:
        result = import_watchlist_csv(session, csv_text)
        session.commit()
        assert result.created == 1
        assert result.errors == ()

        eintraege = _list_watchlist(session)

    assert len(eintraege) == 1
    assert eintraege[0]["Unternehmen"] == "Firma E"
    assert eintraege[0]["Notiz"] == "Beobachten wegen Kursrückgang"


def test_list_watchlist_findet_entity_ueber_bestehende_identifier(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        find_or_create_entity(
            session, name="Firma F (bereits erfasst)",
            identifiers=[IdentifierSpec(id_type=IdentifierType.ISIN, id_value="DE0001234567")],
        )
        session.commit()

        csv_text = "id_type,id_value,name,note\nisin,DE0001234567,Anderer Name,\n"
        result = import_watchlist_csv(session, csv_text)
        session.commit()
        assert result.created == 1

        eintraege = _list_watchlist(session)

    # Der bereits bestehende Entity-Name gewinnt -- der CSV-"name" wird nur
    # verwendet, wenn noch keine Entity zu dieser Kennung existiert.
    assert eintraege[0]["Unternehmen"] == "Firma F (bereits erfasst)"


def test_konzentration_dataframe_skaliert_anteile_auf_prozent() -> None:
    # Regressionstest: ein früherer Entwurf dieser Seite zeigte die
    # Bruchzahlen aus ConcentrationBreakdown.by_key (0..1) unskaliert mit
    # einem "%.1f%%"-Format an -- 0.667 erschien fälschlich als "0.7%" statt
    # "66.7%". Erst beim Live-Test mit echtem Browser aufgefallen (siehe
    # DECISIONS.md ADR-32); dieser Test fängt eine Regression jetzt vorher ab.
    breakdown = ConcentrationBreakdown(
        computable=True, note=None,
        by_key={"Pharma": 2 / 3, "Software": 1 / 3},
        total_value=1500.0, unclassified_value=0.0,
    )

    df = _konzentration_dataframe(breakdown)

    assert list(df["Gruppe"]) == ["Pharma", "Software"]
    assert df.loc[0, "Anteil (%)"] == pytest.approx(200 / 3)
    assert df.loc[1, "Anteil (%)"] == pytest.approx(100 / 3)


def test_drawdown_dataframe_skaliert_max_drawdown_pct_auf_prozent() -> None:
    # Derselbe Skalierungsfehler betraf auch max_drawdown_pct -- trotz des
    # "_pct"-Namens eine Bruchzahl (0..-1), kein bereits skalierter Wert.
    drawdowns = {
        "e1": DrawdownResult(
            computable=True, note=None, max_drawdown_pct=-0.2,
            peak_date=date(2024, 1, 1), trough_date=date(2024, 2, 1),
        ),
    }

    df = _drawdown_dataframe(drawdowns, {"e1": "Firma X"})

    assert df.loc[0, "Unternehmen"] == "Firma X"
    assert df.loc[0, "Max. Drawdown (%)"] == -20.0
