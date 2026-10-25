# T01d – Label-Stichprobe

- **Status:** Offen
- **Schätzung:** 1 h
- **Abhängig von:** T01b
- **ADRs:** 0002, 0004

## Ziel

Eine kleine, schnell zu labelnde Stichprobe, um zu messen, wie viel
Relevantes der Vorfilter übersieht und wie viele Fehltreffer er liefert.

## Umfang

1. **CLI:** Stichprobe `data/label_sample.csv` aus den gespeicherten
   Rohdaten. Die Datei wird versioniert.
2. **Doku:** Architektur-Doku ergänzen

## Label-Stichprobe

- 50 Vorgänge, ca. 70 % Treffer und 30 % Nicht-Treffer, damit auch
  übersehene relevante Vorgänge auffallen
- Treffer stratifiziert nach Gruppe, fester Seed, deterministisch
- Spalten: ID, Datum, Vorgangstyp, Titel, Abstract, Sachgebiet, Gruppen,
  getroffene Begriffe, DIP-Link, leere Spalten `label` und `note`
- `label` hat genau einen Wert: `bank`, `versicherer`, `beide` oder `nein`.
  Regelwerke werden erst gelabelt, wenn ihr Vokabular feststeht (T07).

## Akzeptanzkriterien

- [ ] `make check` grün
- [ ] Tests für: Stichprobe deterministisch und mit Nicht-Treffern
- [ ] Stichprobe aus einem `--months 1`-Lauf erzeugt
- [ ] Architektur-Doku aktualisiert
