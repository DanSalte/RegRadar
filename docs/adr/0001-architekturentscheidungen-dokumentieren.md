# ADR-0001: Architekturentscheidungen als ADRs dokumentieren

- **Status:** Accepted
- **Datum:** 2026-10-01

## Kontext

RegRadar ist ein Portfolio-Projekt. Leser (Recruiter, Hiring Manager, Architekten) sollen nicht nur sehen, *was* gebaut wurde, sondern *warum*. Entscheidungen, die nur im Code stecken, sind für diese Zielgruppe unsichtbar.

## Entscheidung

Jede Entscheidung mit Auswirkung auf Struktur, Kosten, Qualität oder Compliance wird als ADR im Format [MADR](https://adr.github.io/madr/) (vereinfacht) unter `docs/adr/` abgelegt:

- fortlaufend nummeriert, nie gelöscht
- revidierte Entscheidungen bekommen Status `Superseded by ADR-XXXX`
- jede ADR nennt verworfene Alternativen und Konsequenzen

## Konsequenzen

- (+) Entscheidungen sind nachvollziehbar und reviewbar, auch für Leser ohne Code-Kenntnis.
- (+) Spätere Änderungen (z. B. DuckDB → Postgres) werden als bewusste Evolution sichtbar statt als Kurswechsel.
- (−) Pflegeaufwand. Gegenmaßnahme: ADRs kurz halten (max. 1 Seite).
