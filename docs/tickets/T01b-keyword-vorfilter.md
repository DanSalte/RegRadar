# T01b – Keyword-Vorfilter, Explorations-Report und Label-Stichprobe

- **Status:** Offen
- **Schätzung:** 2 h
- **Abhängig von:** T01
- **ADRs:** 0002, 0004, 0005, 0009

## Ziel

Verstehen, wie viel der geladenen Vorgänge für eine Zielgruppe relevant ist,
**bevor** die Taxonomie festgelegt wird. Banken und Versicherer dienen als
Beispiel. Gruppen sind Konfiguration, nicht Code.

## Umfang

1. **Domain:** Keyword-Gruppen und Matcher (reine Logik, ohne I/O)
2. **Keyword-Konfiguration** `config/keywords.yaml`:
   - je Gruppe: `label`, `terms` (Teilstring, Groß-/Kleinschreibung egal),
     `acronyms` (exakt, mit Wortgrenzen), `exclude` (hebt Treffer auf)
   - durchsucht werden: Titel, Abstract, Deskriptoren, Sachgebiete
   - Startgruppen (Beispiel Finanzbranche): DORA/IKT, AI Act,
     Geldwäsche/Sanktionen, Bankaufsicht/Eigenkapital,
     Versicherungsaufsicht, Wertpapiere/Kapitalmarkt,
     Zahlungsverkehr/Krypto, ESG, Finanzaufsicht allgemein,
     Verbraucherschutz Finanzen, Cyber, Rechnungslegung/Meldewesen
3. **CLI:** Report `reports/dip_exploration.md` und Label-Stichprobe
   `data/label_sample.csv` aus den gespeicherten Rohdaten
4. **Doku:** Fachkonzept und Architektur-Doku ergänzen

## Report-Inhalt

- Vorgänge gesamt, Ø pro Woche, Volumen pro Kalenderwoche
- Metadaten-Abdeckung: Anteil gefüllter Felder (abstract, deskriptor,
  sachgebiet)
- Treffer gesamt und pro Keyword-Gruppe, Trefferquote
- In welchem Feld getroffen; Anteil der Treffer nur über Metadaten
- Vorgangstypen: gesamt vs. Treffer
- Top-Sachgebiete der Treffer
- Quellenangabe „Deutscher Bundestag/Bundesrat – DIP“

## Label-Stichprobe

- 50 Vorgänge, ca. 70 % Treffer und 30 % Nicht-Treffer (für Recall-Messung)
- Treffer stratifiziert nach Gruppe, fester Seed, deterministisch
- Spalten: ID, Datum, Vorgangstyp, Titel, Sachgebiet, Gruppen,
  Trefferfelder, DIP-Link, leere Spalten `label_relevant`,
  `label_sector`, `label_regulation`, `note`

## Offene Punkte vor Start

- Sollen `reports/` und `data/label_sample.csv` versioniert oder
  gitignored werden?
- `pyyaml` wieder nutzen und die DEP002-Ausnahme in `pyproject.toml`
  entfernen

## Akzeptanzkriterien

- [ ] `make check` grün
- [ ] Tests für: Wortgrenzen bei Abkürzungen, `exclude`, Stichprobe
      deterministisch und mit Nicht-Treffern
- [ ] Report und Stichprobe aus einem `--months 1`-Lauf erzeugt, Report im
      PR angehängt
- [ ] Fachkonzept und Architektur-Doku aktualisiert
