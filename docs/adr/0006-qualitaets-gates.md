# ADR-0006: Deterministische Qualitäts-Gates für agentisch erzeugten Code

- **Status:** Accepted
- **Datum:** 2026-10-02

## Kontext

Der Code wird überwiegend von Claude Code erzeugt. Review-Zeit ist knapp
(5 h/Woche). Qualität muss daher maschinell und reproduzierbar geprüft
werden, nicht per Augenschein.

## Entscheidung

Dieselben Gates auf drei Ebenen:

1. **Während der Generierung:** Claude-Code-Hooks (nach jeder Änderung Lint
   und Typcheck; vor dem Beenden `make check`, max. 5 Versuche)
2. **Lokal:** pre-commit (schnelle Checks) und pre-push (`make check`)
3. **CI + Branch-Protection:** Merge nach `main` nur per PR mit grüner CI.
   Das ist das verbindliche Gate, da lokale Hooks umgehbar sind.

| Gate | Werkzeug | Schwelle |
|---|---|---|
| Stil, Fehlerklassen | ruff | Zeilenlänge 80 |
| Typen | mypy | `--strict` |
| Tests | pytest | Warnungen = Fehler, kein Netzwerk |
| Testabdeckung | coverage (Branch) | ≥ 80 % gesamt |
| Abdeckung neuer Code | diff-cover | ≥ 90 % |
| Architektur | import-linter | Schichtenvertrag |
| Komplexität | xenon | max. B pro Funktion, Ø A |
| Sicherheit | bandit | keine Funde |
| Abhängigkeiten | deptry | keine ungenutzten/fehlenden |
| Secrets, Home-Pfade | detect-secrets, pygrep | keine Funde |

## Verworfene Alternativen

- **xenon A:** zu streng, führt zu künstlich zerstückeltem Code.
- **Docstring-Pflicht:** Typen und Namen dokumentieren das Was; spart
  Zeilen und Tokens.
- **Mutation-Testing in jedem Lauf:** zu langsam.

## Konsequenzen

- (+) Agent kann ohne Rückfrage iterieren, bis alles grün ist.
- (+) Review konzentriert sich auf Fachlichkeit und Entscheidungen.
- (−) Coverage misst Ausführung, nicht Prüfqualität der Tests.
