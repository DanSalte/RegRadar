# ADR-0003: Ein Ingest-Pfad für Backfill und Delta (Zeitfenster, Überlappung, Idempotenz)

- **Status:** Accepted
- **Datum:** 2026-10-01

## Kontext

Wir brauchen zwei Betriebsarten:

- **Backfill:** historische Daten laden (Exploration, Re-Klassifikation nach Vokabular-Änderung).
- **Delta:** täglich nur Neues und Geändertes holen.

Die DIP-API unterstützt beides über Filter: `f.datum.start/end` (Dokumentdatum) und `f.aktualisiert.start/end` (Änderungszeitpunkt). Änderungen sind laut DIP-Doku erst nach ca. 15 Minuten in der API sichtbar; die Doku empfiehlt überlappende Abfrageintervalle.

## Entscheidung

- **Ein Codepfad**, parametrisiert durch ein `Window(start, end, field)`:
  - Backfill = großes Fenster auf `datum`
  - Delta = kleines Fenster auf `aktualisiert`, Start = letzter erfolgreicher Lauf **minus Überlappung** (Default 1 h)
- **Idempotenz:** Speicherung als Upsert über die Quell-ID (`source`, `id`). Doppelt abgeholte Dokumente erzeugen weder Duplikate noch erneute LLM-Kosten (LLM läuft nur, wenn sich ein Content-Hash ändert).
- **Quellen als Adapter** (Ports & Adapters): jede Quelle implementiert dieselbe Schnittstelle `iter_documents(window)`. DIP ist Adapter 1, EUR-Lex folgt.

## Verworfene Alternativen

- **Getrennte Skripte für Backfill und Delta:** doppelte Logik, Bugs nur in einem Pfad.
- **Exakt anschließende Fenster ohne Überlappung:** verliert Änderungen im 15-Minuten-Verzögerungsfenster.

## Konsequenzen

- (+) Backfill ist jederzeit wiederholbar (z. B. nach Taxonomie-Änderung).
- (+) Neue Quellen ändern den Kern nicht.
- (−) Überlappung erzeugt Mehrfachabrufe. Akzeptabel, da Idempotenz Duplikate verhindert und die API kostenfrei ist.
