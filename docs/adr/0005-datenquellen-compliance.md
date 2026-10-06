# ADR-0005: Datenquellen-Compliance als nicht-funktionale Anforderung

- **Status:** Accepted
- **Datum:** 2026-10-01

## Kontext

RegRadar verarbeitet und veröffentlicht Daten Dritter und reichert sie mit LLM-Ausgaben an. Die Nutzungsbedingungen sind bindend:

- **DIP (Bundestag/Bundesrat):** maschinenlesbare API-Daten dürfen umfassend genutzt und weiterverarbeitet werden. Bei Weitergabe ist die Quelle „Deutscher Bundestag/Bundesrat – DIP“ anzugeben, Veränderungen sind kenntlich zu machen. Untersagt ist Nutzung in sinnentstellendem Zusammenhang oder zur Herabwürdigung von Personen. Quelle: [DIP-Nutzungsbedingungen](https://dip.bundestag.de/documents/nutzungsbedingungen_dip.pdf)
- **EUR-Lex:** Rechtsdokumente sind, sofern nicht anders angegeben, frei weiterverwendbar (Beschluss 2011/833/EU), Quellenangabe erforderlich. Quelle: [EUR-Lex Legal Notice](https://eur-lex.europa.eu/content/help/content/legal-notice/legal-notice.html)

*Hinweis: Dies ist keine Rechtsberatung, sondern die technische Umsetzung der veröffentlichten Bedingungen.*

## Entscheidung

Compliance wird als **prüfbare NFR** umgesetzt, nicht als Fußnote:

1. Jeder Datensatz trägt `source`, `source_id` und `source_url`. Die UI zeigt die Quellenangabe an jedem Eintrag.
2. LLM-Ausgaben werden in eigenen Feldern gespeichert (nie Originalfelder überschreiben) und in der UI als **„maschinell erstellt“** gekennzeichnet.
3. Die Klassifikation ist **themenbezogen und neutral**: keine Bewertung von Parteien, Fraktionen oder Personen. Der Prompt verbietet wertende Aussagen; ein CI-Check prüft Ausgaben auf eine Negativliste.
4. API-Keys kommen aus Umgebungsvariablen bzw. GitHub Secrets, nie aus dem Code.
5. Die DIP-API wird mit Rate-Limit und Backoff angesprochen, um Server-Überlastung auszuschließen.

## Konsequenzen

- (+) Rechtliche Bedingungen sind im Datenmodell und in der CI verankert, nicht nur dokumentiert.
- (+) Zeigt Umgang mit regulatorischen Anforderungen, also genau die Domäne der Zielkunden.
- (−) Zusätzliche Felder und Checks. Geringer Aufwand gemessen am Risiko.
