"""Point-in-time-Universum (Auftrag §9: „Point-in-time-Universum ... einbeziehen,
Look-ahead-, Survivorship- und Selection-Bias verhindern").

Eine ``Entity`` gilt zu einem Stichtag ``as_of`` als „bekannt", wenn zu
diesem Zeitpunkt bereits mindestens ein ``DataPoint`` für sie abgerufen
war (``retrieved_at_utc <= as_of``) — dieselbe Point-in-time-Grundlage,
die ``fundamentals/series.py`` für einzelne Kennzahlen-Zeitreihen nutzt
(ADR-6). Ein Backtest, der für einen Stichtag ausschließlich Entities
aus dieser Funktion verwendet, kann strukturell keinen Kandidaten
einbeziehen, der zu diesem Zeitpunkt noch nicht bekannt war.

**Bewusste, dokumentierte Lücke — Survivorship-Bias nicht vollständig
vermieden:** Diese Funktion verhindert, dass ein SPÄTER bekannt
gewordener Kandidat ein FRÜHERES Ergebnis beeinflusst (Look-ahead-
Schutz, siehe ``tests/backtesting/test_universe.py``). Sie verhindert
NICHT, dass ein zwischenzeitlich aus dem Datenbestand entferntes oder
nie erfasstes, aber historisch tatsächlich existierendes Unternehmen
(z. B. ein später delistetes Unternehmen) fehlt — dafür gibt es keine
angebundene Quelle (SEC EDGAR und Alpha Vantage liefern keine
systematische Delisting-Historie im Kostenlos-Paket, siehe
``DATA_SOURCES.md``). Das Universum dieser Version ist daher
„alles, was das System zum Stichtag bereits erfasst hatte", nicht
„alles, was zum Stichtag historisch am Markt existierte". Dieselbe
Einschränkung gilt für jeden Backtest, der auf dieser Funktion aufbaut
(``backtesting/engine.py``).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from investment_analyzer.entity_resolution.models import Entity
from investment_analyzer.normalization.models import DataPoint


def get_point_in_time_universe(session: Session, as_of: datetime) -> list[Entity]:
    """Liefert alle ``Entity``-Zeilen, für die zum Stichtag ``as_of`` bereits
    mindestens ein Datenpunkt bekannt war — sortiert nach ``Entity.id`` für
    ein deterministisches, reproduzierbares Ergebnis.
    """

    entity_ids = (
        select(DataPoint.entity_id)
        .where(DataPoint.retrieved_at_utc <= as_of)
        .distinct()
        .subquery()
    )
    return list(
        session.scalars(
            select(Entity).where(Entity.id.in_(select(entity_ids.c.entity_id))).order_by(Entity.id)
        ).all()
    )
