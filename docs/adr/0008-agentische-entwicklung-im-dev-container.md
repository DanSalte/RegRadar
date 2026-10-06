# ADR-0008: Agentische Entwicklung im Dev-Container

- **Status:** Accepted
- **Datum:** 2026-10-02

## Kontext

Claude Code soll Tickets eigenständig bis zum PR abarbeiten, ohne
Rückfragen bei jedem Befehl. Gleichzeitig darf es keinen Zugriff auf den
restlichen Rechner (macOS) haben, und persönliche Pfade oder Secrets dürfen
nicht ins Repo gelangen.

## Entscheidung

- Claude Code läuft **ausschließlich im Dev-Container** mit
  `--dangerously-skip-permissions`. Der Container ist eine eigene
  Implementierung (MIT); Claude Code kommt über das offizielle
  Dev-Container-Feature von Anthropic (MIT, nur referenziert).
- **Isolation:** nur das Projekt ist gemountet (`/workspace`), Nicht-Root-
  User ohne allgemeines `sudo` (nur für das Firewall-Skript),
  Default-Deny-Firewall für IPv4 und IPv6 mit Allowlist (Anthropic,
  GitHub, PyPI, DIP-API, VS Code).
- **Keine Host-Secrets** im Container (kein `~/.ssh`, keine Cloud-Logins).
  GitHub-Zugriff über einen fine-grained Token nur für dieses Repo.
  Nach T00 ohne Workflow-Recht, damit der Agent die CI nicht ändern kann.
- **Guard-Hook:** Claude-Code-Tools werden außerhalb des Containers
  blockiert.
- **Merge nur durch den Owner:** Branch-Protection auf `main`, Deny-Regeln
  für Push auf `main` und `gh pr merge`.
- Die DIP-API wird vom Container aus echt aufgerufen. Der Key ist öffentlich,
  Rate-Limit im Code.
- Die Konfiguration von Dev-Container und Claude Code (Hooks, Anweisungen)
  ist Teil der lokalen Entwicklungsumgebung und nicht versioniert.

## Verworfene Alternativen

| Option | Warum nicht |
|---|---|
| Cloud-Session | Gut geeignet, aber Code soll lokal laufen und ausprobiert werden können |
| Anthropics Referenz-Container kopieren | Steht unter „All rights reserved“, passt nicht zur MIT-Lizenz des Repos |
| Nur Bash-Sandbox (`/sandbox`) | Schützt nur Shell-Befehle; Lesen von `~/.ssh` standardmäßig erlaubt |
| Ohne Isolation, mit Rückfragen | Kein autonomes Abarbeiten möglich |

## Konsequenzen

- (+) Autonomes Arbeiten bei begrenztem Schadensradius.
- (−) Alles im Container ist für den Agenten lesbar (inkl. Claude-Login).
  Nur vertrauenswürdige Repos verwenden.
- (−) Firewall löst Domains beim Start auf. Wechselnde IPs (z. B. PyPI-CDN)
  können einen Container-Neustart erfordern.
