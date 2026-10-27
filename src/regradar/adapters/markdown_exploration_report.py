"""Building block (report): renders the exploration report as Markdown."""

from collections import Counter
from collections.abc import Sequence

from regradar.core.application.explore import (
    TOP_SUBJECT_AREAS,
    ExplorationReport,
)
from regradar.core.domain.window import WindowField

SOURCE = "Deutscher Bundestag/Bundesrat – DIP"
WINDOW_FIELD_LABELS = {
    WindowField.DATE: "Datum",
    WindowField.UPDATED: "Aktualisierung",
}
FIELD_LABELS = {
    "title": "Titel",
    "abstract": "Abstract",
    "descriptors": "Deskriptoren",
    "subject_areas": "Sachgebiete",
}


def render_exploration_report(report: ExplorationReport) -> str:
    sections = [
        _overview(report),
        _weeks(report),
        _coverage(report),
        _groups(report),
        _fields(report),
        _procedure_types(report),
        _subject_areas(report),
        f"Quelle: {SOURCE}. Auswertung durch RegRadar.\n",
    ]
    return "\n".join(sections)


def _overview(report: ExplorationReport) -> str:
    window = report.window
    return (
        "# DIP-Exploration\n\n"
        f"Zeitraum: {window.start} bis {window.end} "
        f"(nach {WINDOW_FIELD_LABELS[window.field]})\n\n"
        f"- Vorgänge gesamt: {report.total}\n"
        f"- Ø pro Woche: {_number(report.per_week)}\n"
        f"- Treffer: {report.hits} ({_share(report.hits, report.total)})\n"
    )


def _weeks(report: ExplorationReport) -> str:
    rows = [(week, str(count)) for week, count in sorted(report.weeks.items())]
    return _table("Volumen pro Kalenderwoche", ("Woche", "Vorgänge"), rows)


def _coverage(report: ExplorationReport) -> str:
    rows = [
        (
            FIELD_LABELS[field],
            str(count),
            _share(count, report.total),
        )
        for field, count in report.coverage.items()
    ]
    return _table("Metadaten-Abdeckung", ("Feld", "Vorgänge", "Anteil"), rows)


def _groups(report: ExplorationReport) -> str:
    rows = [
        (group.label, str(count), _share(count, report.total))
        for group, count in report.groups
    ]
    return _table(
        "Treffer pro Keyword-Gruppe",
        ("Gruppe", "Treffer", "Trefferquote"),
        rows,
        note="Ein Vorgang kann mehrere Gruppen treffen.",
    )


def _fields(report: ExplorationReport) -> str:
    rows = [
        (label, str(report.hit_fields[field]))
        for field, label in FIELD_LABELS.items()
    ]
    rows.append(("nur über Metadaten", str(report.metadata_only)))
    return _table(
        "Treffer nach Feld",
        ("Feld", "Vorgänge mit Treffer"),
        rows,
        note="Metadaten sind Deskriptoren und Sachgebiete.",
    )


def _procedure_types(report: ExplorationReport) -> str:
    rows = [
        (
            procedure_type,
            str(total),
            str(report.hit_procedure_types[procedure_type]),
            _share(report.hit_procedure_types[procedure_type], total),
        )
        for procedure_type, total in report.procedure_types.most_common()
    ]
    return _table(
        "Vorgangstypen",
        ("Vorgangstyp", "Gesamt", "Treffer", "Trefferquote"),
        rows,
    )


def _subject_areas(report: ExplorationReport) -> str:
    top: Counter[str] = report.hit_subject_areas
    rows = [
        (area, str(count)) for area, count in top.most_common(TOP_SUBJECT_AREAS)
    ]
    return _table(
        f"Top-{TOP_SUBJECT_AREAS}-Sachgebiete der Treffer",
        ("Sachgebiet", "Treffer"),
        rows,
    )


def _table(
    title: str,
    header: tuple[str, ...],
    rows: Sequence[tuple[str, ...]],
    *,
    note: str = "",
) -> str:
    lines = [
        f"## {title}\n",
        f"| {' | '.join(header)} |",
        f"|{'---|' * len(header)}",
        *(f"| {' | '.join(row)} |" for row in rows),
    ]
    if note:
        lines.append(f"\n{note}")
    return "\n".join(lines) + "\n"


def _share(part: int, whole: int) -> str:
    return _number(part / whole * 100) + " %" if whole else "–"


def _number(value: float) -> str:
    return f"{value:.1f}".replace(".", ",")
