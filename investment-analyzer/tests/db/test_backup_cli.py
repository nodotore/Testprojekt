from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from investment_analyzer.config.settings import get_settings
from investment_analyzer.db import create_all_tables, create_db_engine, create_session_factory
from investment_analyzer.db.backup_cli import main
from investment_analyzer.entity_resolution.models import Entity


def _reset_cache() -> None:
    get_settings.cache_clear()


def _seed_database(data_dir: Path) -> None:
    engine = create_db_engine(f"sqlite:///{data_dir / 'investment_analyzer.db'}")
    create_all_tables(engine)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        session.add(Entity(name="Firma J (CLI-Test)", country="DE"))
        session.commit()
    engine.dispose()


def test_auflisten_ohne_sicherungen(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("IA_DATA_DIR", str(tmp_path))
    _reset_cache()

    exit_code = main(["auflisten"])

    assert exit_code == 0
    assert "Noch keine Sicherungen" in capsys.readouterr().out
    _reset_cache()


def test_sichern_ohne_datenbank_meldet_fehler(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("IA_DATA_DIR", str(tmp_path))
    _reset_cache()

    exit_code = main(["sichern"])

    assert exit_code == 1
    assert "Fehler" in capsys.readouterr().err
    _reset_cache()


def test_sichern_und_auflisten(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("IA_DATA_DIR", str(tmp_path))
    _reset_cache()
    _seed_database(tmp_path)

    exit_code = main(["sichern"])
    assert exit_code == 0
    ausgabe = capsys.readouterr().out
    assert "Sicherung erstellt" in ausgabe

    exit_code = main(["auflisten"])
    ausgabe = capsys.readouterr().out
    assert "investment_analyzer-" in ausgabe
    _reset_cache()


def test_sichern_wiederherstellen_end_zu_end_ueber_cli(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("IA_DATA_DIR", str(tmp_path))
    _reset_cache()
    _seed_database(tmp_path)

    main(["sichern"])
    backup_pfad = next((tmp_path / "backups").glob("investment_analyzer-*.db"))

    (tmp_path / "investment_analyzer.db").write_bytes(b"KORRUPT")

    exit_code = main(["wiederherstellen", str(backup_pfad)])
    assert exit_code == 0
    ausgabe = capsys.readouterr().out
    assert "wiederhergestellt" in ausgabe

    engine = create_db_engine(f"sqlite:///{tmp_path / 'investment_analyzer.db'}")
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        names = set(session.scalars(select(Entity.name)).all())
    engine.dispose()
    assert names == {"Firma J (CLI-Test)"}
    _reset_cache()


def test_wiederherstellen_ohne_vorhandene_sicherung_meldet_fehler(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.setenv("IA_DATA_DIR", str(tmp_path))
    _reset_cache()

    exit_code = main(["wiederherstellen", str(tmp_path / "nicht-vorhanden.db")])

    assert exit_code == 1
    assert "Fehler" in capsys.readouterr().err
    _reset_cache()
