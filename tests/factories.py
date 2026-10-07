from datetime import UTC, date, datetime

from regradar.core.domain.procedure import Procedure

UPDATED = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)


def make_procedure(
    source_id: str = "1",
    *,
    title: str = "Titel",
    abstract: str | None = None,
    day: date | None = date(2026, 9, 1),
) -> Procedure:
    return Procedure(
        source="dip",
        source_id=source_id,
        source_url=f"https://dip.bundestag.de/vorgang/x/{source_id}",
        title=title,
        procedure_type="Gesetzgebung",
        updated=UPDATED,
        date=day,
        abstract=abstract,
    )


def raw_dip(source_id: str = "1", **changes: object) -> dict[str, object]:
    document: dict[str, object] = {
        "id": source_id,
        "titel": "Gesetz zur Umsetzung der DORA-Verordnung",
        "vorgangstyp": "Gesetzgebung",
        "aktualisiert": "2026-09-28T07:11:07+02:00",
        "datum": "2026-09-01",
        "abstract": "Digitale operationale Resilienz",
        "beratungsstand": "Beratung im Ausschuss",
        "sachgebiet": ["Wirtschaft"],
        "deskriptor": [
            {"name": "Kreditinstitut", "typ": "Sachbegriffe", "fundstelle": 1}
        ],
        "initiative": ["Bundesregierung"],
    }
    document.update(changes)
    return document
