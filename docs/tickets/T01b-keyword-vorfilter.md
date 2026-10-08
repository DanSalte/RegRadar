# T01b – Keyword-Vorfilter: Matcher und Konfiguration

- **Status:** Offen
- **Schätzung:** 1 h
- **Abhängig von:** T01
- **ADRs:** 0002, 0004, 0009, 0010

## Ziel

Vorgänge per Keyword-Gruppen vorfiltern. Der Vorfilter spart nur Kosten: Er
soll möglichst nichts Relevantes übersehen und nimmt dafür Fehltreffer in
Kauf (ADR-0010). Banken und Versicherer dienen als Beispiel. Gruppen sind
Konfiguration, nicht Code.

## Umfang

1. **Domain:** `KeywordGroup`, `KeywordHit` (Gruppe, Begriff, Feld) und
   `KeywordMatcher.match(procedure) -> list[KeywordHit]`, reine Logik ohne
   I/O. Der getroffene Begriff wird für `keyword_hits` gebraucht (ADR-0010).
2. **Keyword-Konfiguration** `config/keywords.yaml`:
   - je Gruppe: `label`, `terms` (Teilstring, Groß-/Kleinschreibung egal),
     `acronyms` (exakt, mit Wortgrenzen), `exclude` (kommt ein Begriff
     irgendwo im Vorgang vor, entfallen alle Treffer dieser Gruppe)
   - durchsucht werden: Titel, Abstract, Deskriptoren, Sachgebiete
   - Startgruppen (Beispiel Finanzbranche): DORA/IKT, AI Act,
     Geldwäsche/Sanktionen, Bankaufsicht/Eigenkapital,
     Versicherungsaufsicht, Wertpapiere/Kapitalmarkt,
     Zahlungsverkehr/Krypto, ESG, Finanzaufsicht allgemein,
     Verbraucherschutz Finanzen, Cyber, Rechnungslegung/Meldewesen
3. **Laden der Konfiguration** mit Pydantic; fehlende oder ungültige Datei
   ist ein systemischer Fehler (ADR-0007). `pyyaml` wird genutzt, die
   DEP002-Ausnahme in `pyproject.toml` entfällt.
4. **Doku:** Fachkonzept und Architektur-Doku ergänzen, Abweichung von der
   Schnittstelle in ADR-0004 vermerken

## Akzeptanzkriterien

- [ ] `make check` grün
- [ ] Tests für: Wortgrenzen bei Abkürzungen, Groß-/Kleinschreibung,
      `exclude`, Treffer in jedem Feld, ungültige Konfiguration
- [ ] Fachkonzept und Architektur-Doku aktualisiert
