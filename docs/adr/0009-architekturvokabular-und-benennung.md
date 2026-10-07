# ADR-0009: Architekturvokabular und Benennung

- **Status:** Accepted
- **Datum:** 2026-10-06

## Kontext

Ohne feste Regeln entstehen mehrdeutige Namen: `models.py` klingt nach
Datenbank-Schema, `utils.py` wird zum Sammelbecken, `links.py` klingt nach
Linker. Bei agentischer Entwicklung (ADR-0008) passiert das bei jedem Ticket
neu. Außerdem muss die Architektur (Ports & Adapters) im Code erkennbar sein,
nicht nur in der Doku.

## Entscheidung

1. **Vokabular:** Wir verwenden die Begriffe der hexagonalen Architektur und
   des Domain-Driven Design, wie in [architektur.md](../architektur.md)
   erklärt: Core, Entity, Value Object, Use Case, Port, Driving/Driven Adapter,
   Baustein, Composition Root, DTO, Anti-Corruption Layer, Dead Letter.
2. **Fachbegriff:** Die zentrale Einheit heißt `Procedure` (DIP-Vorgang,
   EUR-Lex-Procedure), nicht `Proceeding`, das im Englischen nach
   Gerichtsverfahren klingt. Siehe [fachkonzept.md](../fachkonzept.md).
3. **Ordner:**
   - `core/domain/` und `core/application/` bilden den Core.
   - Ports liegen in `core/application/ports/`, eine Datei je Port.
     Fehlerklassen liegen getrennt davon in `core/application/errors.py`.
   - `adapters/` enthält die Adapter und ihre Bausteine: ein Ordner je
     Adapter mit eigenen Bausteinen (z. B. `adapters/dip/`), gemeinsame
     Bausteine in `adapters/shared/`.
   - `entrypoints/` enthält Driving Adapter und Composition Root.
4. **Benennungsregeln:**
   - **Ports** heißen nach ihrer Rolle: `ProcedureSource`, `RawStore`,
     `DeadLetterStore`.
   - **Adapter** heißen `<Technik><Port>`: `DipProcedureSource`,
     `JsonlRawStore`, `JsonlDeadLetterStore`.
   - **DTOs** tragen das Suffix `Dto`: `DipProcedureDto`.
   - **Use Cases** heißen nach dem fachlichen Vorgang (Verb): `ingest`.
   - **Dateien** heißen wie ihre Hauptklasse bzw. Hauptfunktion in
     snake_case: `jsonl_raw_store.py`, `web_url.py`.
   - **Funktionen** sagen, was sie tun, nicht wie sie technisch heißen:
     `write_file_atomically`, `procedure_web_url`.
5. **Bausteine** sind keine Adapter: Sie erfüllen keinen Port und werden nie
   vom Core aufgerufen. Jedes Baustein-Modul beginnt mit dem Docstring
   `Building block (…): …`, damit alle Bausteine per Suche auffindbar sind.

## Verworfene Alternativen

- **Flache Ordner ohne `core/`:** Der Core wäre nur in der Doku sichtbar,
  nicht in der Struktur.
- **Feinere Unterordner nach Muster** (`core/domain/entities/`,
  `core/application/use_cases/`, `adapters/driving|driven/`): Bei der
  aktuellen Projektgröße zu viel Verschachtelung.
- **Sammelmodul `utils.py`** für Hilfsfunktionen: wird erfahrungsgemäß zum
  unsortierten Ablageort; Bausteine liegen stattdessen beim Adapter oder in
  `adapters/shared/`.
- **Keine festen Regeln:** führt zu den oben beschriebenen Problemen.

## Konsequenzen

- (+) Namen und Ordner sind ohne Code-Lektüre verständlich und im Review
  prüfbar.
- (+) Neue Quellen, Speicher und Hilfsfunktionen folgen einem bekannten
  Schema.
- (−) Längere Dateinamen und eine Ebene mehr (`core/`).
- (−) `docs/architektur.md` muss mit jedem Ticket gepflegt werden.
