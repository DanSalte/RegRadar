# ADR-0010: Datenfluss und Hosting

- **Status:** Accepted
- **Datum:** 2026-10-07

## Kontext

RegRadar soll Vorgänge filterbar in einem Frontend auf GitHub Pages zeigen.
Rahmenbedingungen: Budget max. 5–10 €/Monat, beteiligt sind nur GitHub, die
DIP-API und eine Datenbank. Der Runner von GitHub Actions ist flüchtig, er
vergisst nach jedem Lauf alles. LLM-Aufrufe kosten Geld und dürfen sich
nicht unnötig wiederholen.

## Entscheidung

### 1. Ablauf eines Laufs

Ein Workflow in GitHub Actions ruft die CLI mit dem Zeitraum auf
(Backfill oder Delta, ADR-0003).

| Schritt | Was passiert | Ergebnis |
|---|---|---|
| Holen | DIP-API, Rohdaten als JSONL im Arbeitsverzeichnis des Laufs | Rohdaten |
| Prüfen | Pydantic; Fehlerhafte in die Dead-Letter-Ablage (ADR-0007) | `Procedure` |
| Vorfiltern | Keyword-Gruppen (ADR-0004); nur Treffer gehen weiter | Treffer |
| Speichern | Upsert in die Tabelle `procedures`; neu oder Titel/Abstract geändert → `classified_at = NULL`. Nachschlagetabellen aus der Konfiguration neu schreiben | Bestand |
| Klassifizieren | LLM nur für `classified_at IS NULL`; geschlossene Vokabulare (ADR-0002), Structured Output | Zielgruppen, Regelwerke |
| Veröffentlichen | Datei als Release-Asset sichern und mit dem Frontend auf Pages deployen | öffentliche Daten |

Der Keyword-Vorfilter spart nur Kosten. Er soll möglichst nichts Relevantes
übersehen und nimmt dafür Fehltreffer in Kauf. Ob ein Vorgang für eine
Zielgruppe relevant ist, entscheidet das LLM.

### 2. Rohdaten und Dead Letters

- Rohdaten sind ein Zwischenstand innerhalb eines Laufs und werden nicht über
  den Lauf hinaus aufbewahrt. Bei Bedarf kommen sie erneut von der API.
- Dead Letters werden ebenfalls nicht aufbewahrt. Fehlgeschlagene Dokumente
  stehen mit ID und Fehler im Actions-Log und in `run_summary`.
- Lokal bleibt die JSONL-Ablage unter `data/raw/` als Cache für die
  Entwicklung.

### 3. Schema der Datenbank (DuckDB)

**Grenze zwischen Konfiguration und Datenbank:** Die Konfiguration
(`config/*.yaml`, versioniert in Git, geändert per PR) enthält die Regeln:
wonach gesucht und wie eingeordnet wird. Die Datenbank enthält die
Ergebnisse eines Laufs. Was ein Mensch bewusst entscheidet, gehört in die
Konfiguration; was ein Lauf erzeugt, in die Datenbank. Damit die Datei für das
Frontend aus sich heraus verständlich ist, schreibt jeder Lauf eine Kopie der
Konfiguration als Nachschlagetabellen hinein. Bearbeitet wird diese Kopie nie.

**Tabelle `procedures`** (Ergebnisse):

| Spalte | Typ | Pflicht | Bedeutung |
|---|---|---|---|
| `source` | VARCHAR | ja | Quelle, z. B. `dip` |
| `source_id` | VARCHAR | ja | ID in der Quelle |
| `title` | VARCHAR | ja | Titel |
| `abstract` | VARCHAR | nein | Kurzbeschreibung; bei DIP nur bei etwa 26 % vorhanden |
| `source_url` | VARCHAR | ja | Link zum Vorgang |
| `date` | DATE | nein | Datum des jüngsten Dokuments im Vorgang |
| `updated` | TIMESTAMP | ja | letzte Änderung in der Quelle (Delta) |
| `procedure_type` | VARCHAR | ja | Vorgangstyp, z. B. Gesetzgebung |
| `status` | VARCHAR | nein | Beratungsstand |
| `keyword_hits` | STRUCT(keyword_group VARCHAR, term VARCHAR)[] | ja | getroffene Begriffe mit ihrer Keyword-Gruppe, nie leer |
| `target_groups` | VARCHAR[] | nein | Zielgruppen laut LLM; leer = für niemanden relevant, NULL = noch nicht klassifiziert |
| `regulations` | VARCHAR[] | nein | Regelwerke laut LLM |
| `classified_at` | TIMESTAMP | nein | Zeitpunkt der Klassifikation; NULL = steht aus |

- Primärschlüssel: (`source`, `source_id`).
- Die Werte von `target_groups` und `regulations` stammen aus geschlossenen
  Vokabularen in der Konfiguration (ADR-0002).
- Deskriptoren, Sachgebiete und Initiative werden nicht gespeichert. Sie
  dienen nur dem Vorfilter beim Ingest.
- Vorgänge, die das LLM für keine Zielgruppe relevant hält, bleiben
  gespeichert. Das Frontend zeigt standardmäßig nur Vorgänge mit nicht
  leeren `target_groups`.
- Aus `keyword_hits` und `target_groups` lässt sich je Begriff ablesen, wie
  viele seiner Treffer das LLM für relevant hält. Das ist die Grundlage, um
  Keywords nachzuschärfen (T02).

**Nachschlagetabellen** (Kopie der Konfiguration, bei jedem Lauf neu
geschrieben):

| Tabelle | Spalten | Inhalt |
|---|---|---|
| `keyword_groups` | `name`, `label`, `terms`, `acronyms`, `exclude` | Keyword-Gruppen mit ihren Begriffen |
| `vocabulary` | `kind` (`target_group` oder `regulation`), `name`, `label` | erlaubte Werte für die Einordnung durch das LLM |

### 4. Neu-Klassifikation

- `classified_at` wird zurückgesetzt, wenn ein Vorgang neu ist oder sich
  Titel oder Abstract ändern. Statusänderungen lösen keinen LLM-Aufruf aus.
- Ändern sich Keywords oder Vokabulare, läuft ein Backfill (ADR-0003).
  Nicht-Treffer sind nicht gespeichert und werden dafür neu geholt.

### 5. Speicherort und Veröffentlichung

- Die DuckDB-Datei liegt zwischen den Läufen als Asset eines festen
  GitHub-Releases. Jeder Lauf lädt sie herunter, aktualisiert sie und lädt
  sie wieder hoch.
- Es läuft immer nur ein Lauf zugleich (Concurrency-Gruppe im Workflow).
- Dieselbe Datei geht mit dem Frontend auf GitHub Pages; es gibt keinen
  separaten Export. Die Daten sind öffentlich, mit Quellenangabe nach
  ADR-0005.

### 6. Frontend

- Eigener Ordner `web/`, statisch. Es liest die Datei per DuckDB-WASM und
  filtert im Browser.
- Das Frontend ist **kein Adapter** des Python-Hexagons, sondern eine eigene
  Anwendung. Adapter sind der Speicher-Adapter, der die Datei schreibt, und
  der LLM-Adapter.
- Das Schema aus Punkt 3, einschließlich der Nachschlagetabellen, ist der
  Vertrag zwischen Ingest und Frontend.
  Änderungen gehen über eine Folge-ADR, und das Frontend zieht mit.

### 7. Änderung an ADR-0007

Dead Letters werden nicht im nächsten Lauf erneut versucht. Ein Dokument
scheitert bei uns an der Prüfung, und das passiert bei unveränderten Daten
jedes Mal wieder; Netzwerkfehler fängt bereits der Retry ab. Korrigiert die
Quelle das Dokument, ändert sich `aktualisiert`, und der nächste Delta-Lauf
holt es automatisch neu.

## Verworfene Alternativen

| Option | Warum nicht |
|---|---|
| Externe Datenbank (Postgres, Supabase, Neon) mit Server oder Grafana | weiterer Anbieter, Zugangsdaten, abgesicherter Lesezugriff; Mehrwert erst bei Schreibzugriffen von Nutzern oder großen Datenmengen |
| Datei in einem Branch `data` committen | eine täglich geänderte Binärdatei bläht die Historie auf |
| Actions-Cache oder Artifact | laufen ab |
| Alle Vorgänge speichern | größere Datei; ein Backfill ist günstig (etwa 2 Minuten für 6 Monate) |
| Irrelevante Vorgänge löschen | würden bei jeder Änderung erneut klassifiziert; die LLM-Entscheidung wäre für das Eval (T08) nicht mehr prüfbar |
| Nur die Namen der getroffenen Gruppen speichern | nicht messbar, welcher Begriff relevante Treffer liefert und welcher nur Fehltreffer |
| Konfiguration nicht in die Datenbank kopieren | das Frontend kennt die Konfiguration nicht und könnte weder Labels noch Begriffe anzeigen |
| Bei jeder Änderung neu klassifizieren | der Beratungsstand ändert sich oft; Kosten ohne Mehrwert |
| Dead Letters aufbewahren und erneut versuchen | mehr Logik in Workflow und Use Case für Fehler, die sich ohne Änderung der Quelle wiederholen |

## Trigger für Revision

- Nutzer sollen selbst Daten schreiben (Konten, gespeicherte Profile).
- Die Datei wird für den Browser zu groß (Hunderte MB).

## Konsequenzen

- (+) 0 € Betrieb, kein Server, kein Schlüssel im Browser.
- (+) LLM-Kosten nur für neue oder inhaltlich geänderte Treffer.
- (+) Der Speicher bleibt austauschbar, weil er hinter einem Port liegt.
- (+) Je Begriff messbar, ob er relevante Treffer liefert.
- (−) Bei geänderten Keywords oder Vokabularen ist ein Backfill nötig. Bis
  dahin passen ältere Zeilen nicht ganz zu den Nachschlagetabellen.
- (−) Der Workflow braucht Schreibrecht auf Releases (`contents: write`).
- (−) Gleichzeitige Läufe müssen ausgeschlossen werden.
- (−) Dead Letters sind nach dem Lauf nur noch im Log sichtbar.
