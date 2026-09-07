"""Datenbank-Grundgerüst: Base, Engine/Session-Erzeugung, Metadaten-Registry.

Provenienz-first-Prinzip (siehe DECISIONS.md ADR-6): Alle Domänenmodelle
(``Entity``/``EntityIdentifier`` in ``entity_resolution``, ``Source`` in
``connectors``, ``DataPoint`` in ``normalization``, ``AuditLogEntry`` in
``audit``, ``NewsItem`` in ``news``, ``WatchlistEntry``/
``PortfolioPosition`` in ``portfolio``) registrieren sich auf derselben
``Base.metadata`` und werden hier zentral importiert, damit sowohl
Alembic-Autogenerate als auch ``create_all`` in Tests alle Tabellen kennen.

Dieses Modul ist bewusst dialektunabhängig gehalten (kein SQLite- oder
PostgreSQL-spezifischer Code), damit dieselben Modelle unverändert gegen
SQLite (lokale Entwicklung) und PostgreSQL (Produktion) funktionieren
(Auftrag §4, ADR-2).
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Gemeinsame Basisklasse aller ORM-Modelle."""


def register_all_models() -> None:
    """Importiert alle Modul-Modelle, damit sie auf ``Base.metadata`` erscheinen.

    Muss vor jedem ``Base.metadata.create_all(...)`` oder Alembic-Autogenerate
    aufgerufen werden. Lokale Importe, um Zirkularimporte beim Paketaufbau
    zu vermeiden.
    """

    from investment_analyzer.audit import models as _audit_models  # noqa: F401
    from investment_analyzer.connectors import models as _connectors_models  # noqa: F401
    from investment_analyzer.entity_resolution import (
        models as _entity_resolution_models,  # noqa: F401
    )
    from investment_analyzer.news import models as _news_models  # noqa: F401
    from investment_analyzer.normalization import models as _normalization_models  # noqa: F401
    from investment_analyzer.portfolio import models as _portfolio_models  # noqa: F401


def create_db_engine(database_url: str, *, echo: bool = False) -> Engine:
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, echo=echo, connect_args=connect_args)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


def create_all_tables(engine: Engine) -> None:
    """Nur für Tests/Dev-Bootstrap; produktiv werden Alembic-Migrationen verwendet."""

    register_all_models()
    Base.metadata.create_all(engine)


@contextmanager
def session_scope(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    """Transaktions-Kontextmanager: Commit bei Erfolg, Rollback bei Fehler."""

    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
