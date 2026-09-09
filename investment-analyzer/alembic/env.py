from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Erlaubt den Import von investment_analyzer, auch wenn Alembic von
# außerhalb einer aktivierten venv/eines installierten Pakets läuft
# (Windows-Startskript ruft Alembic aus dem Projektverzeichnis auf).
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from investment_analyzer.config import get_settings  # noqa: E402
from investment_analyzer.db import Base, register_all_models  # noqa: E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

register_all_models()
target_metadata = Base.metadata

# Die tatsächliche DB-URL kommt aus AppSettings (Umgebungsvariable
# IA_DATABASE_URL bzw. lokale SQLite-Datei), nicht aus alembic.ini —
# so bleibt eine einzige Quelle der Wahrheit für die Verbindung
# (siehe investment_analyzer.config.settings.AppSettings).
_settings = get_settings()
# Muss VOR dem ersten Verbindungsaufbau laufen: bei einer lokalen
# SQLite-Datenbank existiert data_dir (z. B. %USERPROFILE%\
# InvestmentAnalyzer) beim allerersten Start auf einem frischen Rechner
# noch nicht. sqlite3 legt das übergeordnete Verzeichnis nicht selbst
# an -- ohne dies schlägt die Migration mit "unable to open database
# file" fehl (in freier Wildbahn gefunden: start.ps1 ruft die Migration
# auf, BEVOR ui/bootstrap.py beim Start der Oberfläche ensure_data_dirs()
# aufruft).
_settings.ensure_data_dirs()
config.set_main_option("sqlalchemy.url", _settings.resolved_database_url)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
