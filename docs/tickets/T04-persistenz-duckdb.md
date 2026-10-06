# T04 – Persistenz in DuckDB mit Upsert, ADR DuckDB vs. Postgres

- **Status:** Entwurf
- **Schätzung:** 2 h
- **Abhängig von:** T01

Wird ausgearbeitet, wenn das Ticket dran ist. Bis dahin werden hier
Anforderungen gesammelt, die sich aus früheren Tickets ergeben.

## Vorgemerkte Akzeptanzkriterien

- [ ] Die Lauf-Bilanz (ADR-0007) zählt `stored` aus der Rückmeldung des
      Speichers (tatsächlich geschriebene bzw. per Upsert aktualisierte
      Datensätze), nicht aus einem Zähler im Use Case. Nur so erkennt der
      Abgleich `loaded = stored + discarded + failed`, wenn beim Schreiben
      Datensätze verloren gehen. Test: ein Speicher-Fake, der einen Datensatz
      verliert, lässt den Lauf mit Exit-Code 1 scheitern.
