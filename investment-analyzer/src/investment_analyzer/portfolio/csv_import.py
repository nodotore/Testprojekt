"""CSV-Import für Watchlist und Portfolio (Auftrag §8: „manuell oder per CSV importieren").

Erwartetes CSV-Format (Kopfzeile Pflicht, Komma-getrennt):

- Watchlist: ``id_type,id_value,name,note``
- Portfolio: ``id_type,id_value,name,quantity,average_cost,currency,note``

``id_type`` ist eine der stabilen Kennungen aus
``entity_resolution.models.IdentifierType`` (ISIN, LEI oder CIK) — ein
Ticker allein wird abgelehnt (Auftrag §5, dieselbe Regel wie bei jeder
anderen Entity-Auflösung). ``name`` wird nur verwendet, wenn für die
Kennung noch keine ``Entity`` existiert.

Jede fehlerhafte Zeile wird gesammelt zurückgegeben statt den ganzen
Import abzubrechen ODER die Zeile stillschweigend zu überspringen
(Auftrag §4 „Fail loud, nicht silent" — hier auf Zeilenebene: der
Aufrufer sieht explizit, welche Zeilen warum nicht importiert wurden).
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from investment_analyzer.entity_resolution.models import IdentifierType
from investment_analyzer.entity_resolution.service import IdentifierSpec, find_or_create_entity
from investment_analyzer.portfolio.models import PortfolioPosition, WatchlistEntry

#: Nur stabile Kennungen sind für den Import zulässig (Auftrag §5) — dieselbe
#: Menge wie ``entity_resolution.service.STABLE_IDENTIFIER_TYPES``, hier
#: separat gehalten, um keine Abhängigkeit auf ein internes Detail des
#: Service-Moduls einzugehen.
STABLE_ID_TYPES = frozenset({IdentifierType.ISIN, IdentifierType.LEI, IdentifierType.CIK})


@dataclass(frozen=True)
class CsvImportError:
    row_number: int  # 1-basiert; Kopfzeile ist Zeile 1, erste Datenzeile ist Zeile 2.
    message: str


@dataclass(frozen=True)
class CsvImportResult:
    created: int
    updated: int
    errors: tuple[CsvImportError, ...]


def _parse_id_type(raw: str) -> str | None:
    normalized = raw.strip().lower()
    return normalized if normalized in STABLE_ID_TYPES else None


def _missing_header_result(required: set[str]) -> CsvImportResult:
    return CsvImportResult(
        created=0,
        updated=0,
        errors=(
            CsvImportError(
                row_number=1,
                message=f"Kopfzeile muss mindestens folgende Spalten enthalten: {sorted(required)}.",
            ),
        ),
    )


def import_watchlist_csv(session: Session, csv_text: str) -> CsvImportResult:
    """Importiert Watchlist-Einträge aus CSV-Text (Spalten: ``id_type,id_value,name,note``)."""

    required = {"id_type", "id_value", "name"}
    reader = csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
        return _missing_header_result(required)

    created = 0
    updated = 0
    errors: list[CsvImportError] = []

    for row_number, row in enumerate(reader, start=2):
        id_type = _parse_id_type(row.get("id_type") or "")
        id_value = (row.get("id_value") or "").strip()
        name = (row.get("name") or "").strip()
        note = (row.get("note") or "").strip() or None

        if id_type is None:
            errors.append(
                CsvImportError(
                    row_number,
                    f"Unbekannter oder fehlender id_type: {row.get('id_type')!r} "
                    "(erlaubt: isin, lei, cik).",
                )
            )
            continue
        if not id_value:
            errors.append(CsvImportError(row_number, "id_value darf nicht leer sein."))
            continue
        if not name:
            errors.append(CsvImportError(row_number, "name darf nicht leer sein."))
            continue

        try:
            entity = find_or_create_entity(
                session, name=name, identifiers=[IdentifierSpec(id_type, id_value)]
            )
        except ValueError as exc:
            errors.append(CsvImportError(row_number, str(exc)))
            continue

        existing = session.scalars(
            select(WatchlistEntry).where(WatchlistEntry.entity_id == entity.id)
        ).first()
        if existing is None:
            session.add(WatchlistEntry(entity_id=entity.id, note=note))
            created += 1
        else:
            existing.note = note
            updated += 1

    return CsvImportResult(created=created, updated=updated, errors=tuple(errors))


def import_portfolio_csv(session: Session, csv_text: str) -> CsvImportResult:
    """Importiert Portfolio-Bestände aus CSV-Text.

    Spalten: ``id_type,id_value,name,quantity,average_cost,currency,note``
    (``average_cost`` und ``note`` optional/leer zulässig).
    """

    required = {"id_type", "id_value", "name", "quantity", "currency"}
    reader = csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
        return _missing_header_result(required)

    created = 0
    updated = 0
    errors: list[CsvImportError] = []

    for row_number, row in enumerate(reader, start=2):
        id_type = _parse_id_type(row.get("id_type") or "")
        id_value = (row.get("id_value") or "").strip()
        name = (row.get("name") or "").strip()
        currency = (row.get("currency") or "").strip().upper()
        note = (row.get("note") or "").strip() or None

        if id_type is None:
            errors.append(
                CsvImportError(
                    row_number,
                    f"Unbekannter oder fehlender id_type: {row.get('id_type')!r} "
                    "(erlaubt: isin, lei, cik).",
                )
            )
            continue
        if not id_value:
            errors.append(CsvImportError(row_number, "id_value darf nicht leer sein."))
            continue
        if not name:
            errors.append(CsvImportError(row_number, "name darf nicht leer sein."))
            continue
        if len(currency) != 3:
            errors.append(
                CsvImportError(row_number, f"currency muss ein 3-Buchstaben-Code sein: {currency!r}.")
            )
            continue

        try:
            quantity = float(row.get("quantity") or "")
        except ValueError:
            errors.append(
                CsvImportError(row_number, f"quantity ist keine gültige Zahl: {row.get('quantity')!r}.")
            )
            continue
        if quantity <= 0:
            errors.append(CsvImportError(row_number, "quantity muss größer als 0 sein."))
            continue

        average_cost_raw = (row.get("average_cost") or "").strip()
        average_cost: float | None = None
        if average_cost_raw:
            try:
                average_cost = float(average_cost_raw)
            except ValueError:
                errors.append(
                    CsvImportError(row_number, f"average_cost ist keine gültige Zahl: {average_cost_raw!r}.")
                )
                continue

        try:
            entity = find_or_create_entity(
                session, name=name, identifiers=[IdentifierSpec(id_type, id_value)]
            )
        except ValueError as exc:
            errors.append(CsvImportError(row_number, str(exc)))
            continue

        existing = session.scalars(
            select(PortfolioPosition).where(PortfolioPosition.entity_id == entity.id)
        ).first()
        if existing is None:
            session.add(
                PortfolioPosition(
                    entity_id=entity.id,
                    quantity=quantity,
                    average_cost=average_cost,
                    currency=currency,
                    note=note,
                )
            )
            created += 1
        else:
            existing.quantity = quantity
            existing.average_cost = average_cost
            existing.currency = currency
            existing.note = note
            updated += 1

    return CsvImportResult(created=created, updated=updated, errors=tuple(errors))
