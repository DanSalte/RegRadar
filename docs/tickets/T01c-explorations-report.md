# T01c – Explorations-Report

- **Status:** Offen
- **Schätzung:** 1 h
- **Abhängig von:** T01b
- **ADRs:** 0004, 0005

## Ziel

Verstehen, wie viel der geladenen Vorgänge der Vorfilter trifft, **bevor**
die Taxonomie festgelegt wird.

## Umfang

1. **CLI:** Report `reports/dip_exploration.md` aus den gespeicherten
   Rohdaten. `reports/` ist gitignored.
2. **Doku:** Architektur-Doku ergänzen

## Report-Inhalt

- Vorgänge gesamt, Ø pro Woche, Volumen pro Kalenderwoche
- Metadaten-Abdeckung: Anteil gefüllter Felder (abstract, deskriptor,
  sachgebiet)
- Treffer gesamt und pro Keyword-Gruppe, Trefferquote
- In welchem Feld getroffen; Anteil der Treffer nur über Metadaten
- Vorgangstypen: gesamt vs. Treffer
- Top-Sachgebiete der Treffer
- Quellenangabe „Deutscher Bundestag/Bundesrat – DIP“

## Akzeptanzkriterien

- [ ] `make check` grün
- [ ] Report aus einem `--months 1`-Lauf erzeugt, im PR angehängt
- [ ] Architektur-Doku aktualisiert
