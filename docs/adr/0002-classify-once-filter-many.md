# ADR-0002: "Classify once, filter many" mit festen Vokabularen

- **Status:** Accepted
- **Datum:** 2026-10-01

## Kontext

Regulatorische Dokumente erscheinen täglich in hoher Zahl (allein die EBA veröffentlichte 2025 über 400 regulatorische Outputs). Verschiedene Nutzer (Compliance einer Bank, IT-Security eines Versicherers, …) brauchen unterschiedliche Ausschnitte. Zwei Varianten waren denkbar:

1. **Filter pro Nutzer beim Ingest:** jedes Profil klassifiziert jedes Dokument selbst.
2. **Einmal allgemein klassifizieren, beim Lesen filtern.**

## Entscheidung

Variante 2. Jedes Dokument wird beim Ingest **einmal** auf festen Dimensionen angereichert:

| Dimension | MVP | Quelle |
|---|---|---|
| Sektor (Kreditinstitute, Versicherer, Wertpapierfirmen, Zahlungsdienste/Krypto, Fonds) | ✅ | LLM |
| Regelwerk/Thema (DORA, AI Act, AML, CRR/CRD, Solvency II, ESG, MiCA, …) | ✅ | Keywords + Metadaten, LLM nur bei Unklarheit |
| Status (Entwurf, Konsultation, verabschiedet, in Kraft, …) | ✅ | Metadaten (deterministisch) |
| Betroffene Funktion (Compliance, IT, Risk, Meldewesen, Recht) | v2 | LLM |
| Dringlichkeit | v2 | **berechnet** aus Status + Frist, nicht geraten |

Alle Dimensionen nutzen **geschlossene Vokabulare** (Enums). Das LLM liefert ausschließlich erlaubte Werte (Structured Output). Profile sind reine Filterausdrücke über diese Dimensionen.

## Verworfene Alternativen

- **Freie Tags vom LLM:** nicht filterbar, nicht messbar, driftet über die Zeit.
- **Klassifikation pro Profil:** Kosten wachsen mit Anzahl Profile × Dokumente.

## Konsequenzen

- (+) Ein neues Profil kostet 0 LLM-Calls. Ingest und Konsum sind entkoppelt.
- (+) Klassifikationsqualität ist pro Dimension gegen ein gelabeltes Testset messbar (CI-Eval).
- (−) Das Vokabular muss gepflegt werden. Änderungen erfordern ggf. Re-Klassifikation (Backfill-Pfad, siehe ADR-0003).
