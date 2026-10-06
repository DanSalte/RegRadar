# T01 – DIP-Ingest-Grundgerüst

- **Status:** In Review
- **Schätzung:** 3 h
- **Abhängig von:** T00
- **ADRs:** 0003, 0005, 0007, 0009

## Ziel

Modulares Grundgerüst für den Ingest nach Ports & Adapters: Vorgänge aus der
DIP-API holen, an der Systemgrenze prüfen, Rohdaten speichern, Fehler nach
ADR-0007 behandeln, alles getestet. Noch kein Filtern, kein LLM, keine
Datenbank. Der Code ist unabhängig von GitHub Actions, lässt sich aber über
die CLI leicht dort einbinden.

## Kontext

- API: `https://search.dip.bundestag.de/api/v1`, OpenAPI-Spezifikation
  unter `https://search.dip.bundestag.de/api/v1/openapi.yaml`
- Endpunkt `vorgang`, Filter `f.datum.start/end` (Backfill) bzw.
  `f.aktualisiert.start/end` (Delta), max. 100 Einträge pro Seite
- Paginierung: gleiche Parameter plus `cursor` erneut senden, bis sich der
  Cursor nicht mehr ändert
- Relevante Felder: `id`, `titel`, `abstract`, `vorgangstyp`, `datum`,
  `sachgebiet` (Liste), `deskriptor` (Liste mit `name`, `typ`,
  `fundstelle`), `initiative`, `beratungsstand`

## Umfang

1. **Domain:** Entity `Procedure`, Value Object `Window` (Start, Ende, Feld
   `datum` oder `aktualisiert`)
2. **Use Case `ingest`** mit Ports `ProcedureSource`, `RawStore`,
   `DeadLetterStore`; Duplikate verwerfen, Lauf-Bilanz
3. **Adapter DIP:** HTTP-Client mit Rate-Limit (1 Anfrage/s), Retry mit
   exponentiellem Backoff bei 429/5xx und Netzwerkfehlern, kein Retry bei
   4xx. Antworten mit Pydantic validieren und auf englische Modellfelder
   mappen.
4. **Rohdatenablage** als JSONL unter `data/raw/` (gitignored), atomar
   geschrieben; ohne `--refresh` keine API-Aufrufe
5. **CLI** `regradar ingest-dip --months N | --start/--end [--refresh]`
6. **Fehlerbehandlung nach ADR-0007:** fehlerhafte Einzeldokumente →
   Dead-Letter-Datei, Lauf geht weiter, Zusammenfassung am Ende, Exit-Code
7. **Doku:** `docs/fachkonzept.md`, `docs/architektur.md`, ADR-0009

## Akzeptanzkriterien

- [x] `make check` grün
- [x] Adapter-Tests mit VCR-Cassette (echte Antwort, Key gefiltert)
- [x] Tests für: Paginierung, Retry (429, Netzwerkfehler), kein Retry bei
      401, Rate-Limit, Dead-Letter, Duplikate, Abbruch bei systemischen
      Fehlern
- [x] Lauf mit `--months 1` erfolgreich, Rohdaten gespeichert
- [x] Zweiter Lauf ohne `--refresh` macht keine API-Aufrufe (Test)
- [x] Link-Format für DIP-Vorgänge verifiziert (im PR dokumentieren)
- [x] Fachkonzept und Architektur-Doku vorhanden, Benennung nach ADR-0009
- [x] Lauf über 6 Monate führt der Owner selbst durch
