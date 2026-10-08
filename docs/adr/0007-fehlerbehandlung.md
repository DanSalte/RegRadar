# ADR-0007: Fehlerbehandlung – nicht abstürzen, nichts verschlucken

- **Status:** Accepted; erneuter Versuch von Dead Letters ersetzt durch
  [ADR-0010](0010-datenfluss-und-hosting.md)
- **Datum:** 2026-10-02

## Kontext

Die Pipeline läuft unbeaufsichtigt (täglicher Cron). Zwei Risiken:
ein Einzelfehler bricht den ganzen Lauf ab, oder Fehler bleiben unbemerkt
und Daten fehlen still.

## Entscheidung

- **Fehlerisolation pro Dokument:** Fehler werden mit Stacktrace geloggt
  (`log.exception`), das Dokument landet in einer Dead-Letter-Ablage, der
  Lauf geht weiter. Dead Letters werden im nächsten Lauf erneut versucht.
- **Abbruch nur bei systemischen Fehlern:** ungültiger Key, API dauerhaft
  nicht erreichbar, fehlende Konfiguration.
- **Abgleich pro Lauf:** geladen = gespeichert + verworfen + fehlgeschlagen.
  Geht er nicht auf, ist der Lauf fehlgeschlagen.
- **Schwelle:** Fehlerquote > 5 % → Exit ≠ 0 (Job rot, Mail von GitHub).
  Darunter Exit 0 mit sichtbarer Warnung.
- **Freshness-Check:** keine neuen Dokumente seit N Tagen → Alarm.
- **Statisch erzwungen** über ruff: kein nacktes/pauschales `except` ohne
  Logging, kein `except: pass`, kein `return` in `finally`,
  `raise ... from`, `contextlib.suppress` verboten.
- **Logging:** structlog, JSON, damit Fehler maschinell auswertbar sind.

## Konsequenzen

- (+) Teilergebnisse statt Totalausfall; jeder Fehler ist sichtbar.
- (+) „Logging-Abdeckung“ indirekt messbar: Branch-Coverage verlangt, dass
  jeder `except`-Zweig getestet wird.
- (−) Dead-Letter-Ablage muss beobachtet werden (Teil des Lauf-Reports).
