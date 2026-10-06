# ADR-0004: Keyword-Vorfilter lokal statt Elasticsearch im MVP

- **Status:** Accepted (für Spike und MVP), Revision bei Erreichen der Trigger unten
- **Datum:** 2026-10-01

## Kontext

Für die Exploration (Ticket 1) und später als günstiger Vorfilter vor dem LLM brauchen wir eine Stichwortsuche über Titel, Abstract und Schlagworte. Naheliegend wäre Elasticsearch/OpenSearch.

Rahmenbedingungen: Budget max. 5–10 €/Monat, Hosting auf GitHub Pages/Actions, Volumen im Bereich weniger tausend Dokumente pro Quartal.

## Entscheidung

- Keyword-Gruppen werden in `config/keywords.yaml` gepflegt (je Gruppe: Begriffe für Teilstring-Suche, Abkürzungen mit Wortgrenzen).
- Das Matching läuft **lokal in Python** hinter einer schmalen Schnittstelle (`KeywordMatcher.match(doc) -> {gruppe: [felder]}`).
- Persistente Volltextsuche im Produkt übernimmt später DuckDB (FTS-Extension), im Browser via DuckDB-WASM.

## Verworfene Alternativen

| Option | Warum nicht (jetzt) |
|---|---|
| Elasticsearch/OpenSearch selbst gehostet | Dauerhaft laufender Server, RAM-hungrig, bricht das 0-€-Hosting-Modell |
| Managed Search (Elastic Cloud, Algolia o. ä.) | Laufende Kosten bzw. Free-Tier-Abhängigkeit für ein Volumen, das in-memory passt |
| Suche über DIP-API-Parameter | Die API bietet keine allgemeine Stichwortsuche über Abstract und Schlagworte; nur strukturierte Filter |

## Trigger für Revision

- Volltextsuche über **Dokument-Volltexte** (nicht nur Metadaten) wird Produktanforderung, **oder**
- Korpus > ca. 1 Mio. Dokumente bzw. Ranking/Relevanz-Scoring (BM25, Synonyme, Stemming) wird nötig.

Dann: OpenSearch als eigener Adapter hinter derselben Schnittstelle.

## Konsequenzen

- (+) 0 € Betriebskosten, deterministisch, in der CI testbar.
- (+) Austauschbar, da Konsumenten nur die Schnittstelle kennen.
- (−) Kein Stemming/Ranking. Für einen Vorfilter mit hoher Recall-Priorität akzeptabel; Präzision liefert später die LLM-Klassifikation.
