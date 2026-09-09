from __future__ import annotations

from pathlib import Path

from investment_analyzer.config.secrets import SecretStore
from investment_analyzer.config.settings import AppSettings
from investment_analyzer.db import create_all_tables, create_db_engine
from investment_analyzer.ui.bootstrap import bootstrap, check_database_ready


def test_check_database_ready_false_ohne_migration(tmp_path: Path) -> None:
    engine = create_db_engine(f"sqlite:///{tmp_path / 'db.sqlite'}")
    assert check_database_ready(engine) is False


def test_check_database_ready_true_nach_create_all(tmp_path: Path) -> None:
    engine = create_db_engine(f"sqlite:///{tmp_path / 'db.sqlite'}")
    create_all_tables(engine)
    assert check_database_ready(engine) is True


def test_bootstrap_erstellt_datenverzeichnisse_und_kontext(tmp_path: Path) -> None:
    settings = AppSettings(data_dir=tmp_path)
    ctx = bootstrap(settings)
    try:
        assert settings.data_dir.exists()
        assert settings.log_dir.exists()
        assert ctx.profile_store.path == settings.profile_path
        assert ctx.profile_store.load_or_none() is None
        # secret_store ist None, falls kein OS-Keyring verfügbar ist (z. B. in
        # dieser Sandbox) -- bootstrap() darf dafür NIE abstürzen (siehe
        # get_secret_store-Tests in tests/config/test_secrets.py für die
        # beiden Backend-Zweige selbst).
        assert ctx.secret_store is None or isinstance(ctx.secret_store, SecretStore)
    finally:
        for handler in list(ctx.logger.handlers):
            handler.close()
            ctx.logger.removeHandler(handler)
        ctx.engine.dispose()
