# T00 – Projektgerüst und Qualitäts-Gates

- **Status:** Erledigt
- **Schätzung:** 3 h
- **ADRs:** 0006, 0007

## Ziel

Leeres, lauffähiges Python-Projekt mit allen Qualitäts-Gates, sodass ab T01
jedes Ticket automatisch geprüft wird. **Kein Anwendungscode** außer einem
Platzhalter-Modul samt Test, damit alle Gates etwas zu prüfen haben.

## Umfang

### 1. Projekt

- `pyproject.toml` mit uv, `requires-python = ">=3.14"`, Paket unter
  `src/regradar/` mit den Unterpaketen `core/domain`, `core/application`,
  `adapters`, `entrypoints`
- Laufzeit-Abhängigkeiten: `pydantic`, `pydantic-settings`, `structlog`,
  `httpx`, `pyyaml`
- Dev-Abhängigkeiten: `pytest`, `pytest-cov`, `pytest-recording`, `ruff`,
  `mypy`, `types-pyyaml`, `diff-cover`, `import-linter`, `xenon`, `bandit`,
  `deptry`, `detect-secrets`, `pre-commit`
- `.gitignore`, `.env.example` (aus Repo übernehmen)

### 2. ruff (`ruff.toml`)

- `line-length = 80`, `target-version = "py314"`
- Regelsatz: `E, W, F, I, N, UP, B, A, C4, SIM, RET, PT, ANN, S, BLE,
  TRY, ERA, C90, PL, PTH, TID`
- Fehlerbehandlung explizit aktiv: `E722, BLE001, S110, S112, TRY400,
  B012, B904`
- `flake8-tidy-imports.banned-api`: `contextlib.suppress`
- `mccabe.max-complexity = 10`
- Prüfen, dass BLE001 `structlog`-Aufrufe `log.exception(...)` als Logging
  erkennt (ggf. `lint.logger-objects`).
- In `tests/`: `S101` (assert) erlaubt, `ANN` gelockert

### 3. mypy (`mypy.ini`)

- `strict = True`, Pydantic-Plugin aktiv, `src/` und `tests/`

### 4. pytest und Coverage

- `--block-network`, `-W error`, Marker `live` registriert und standardmäßig
  ausgeschlossen
- Coverage: `branch = true`, `fail_under = 80`, Report als `coverage.xml`
- `diff-cover coverage.xml --compare-branch=origin/main --fail-under=90`

### 5. Architektur und Komplexität

- `.importlinter`: Layers-Vertrag
  `entrypoints > adapters > core.application > core.domain`, plus Vertrag
  „core.domain importiert weder `httpx` noch `pydantic_settings` noch
  `structlog`“
- `xenon --max-absolute B --max-average A src`
- `bandit -r src`, `deptry .`

### 6. Leaks

- `detect-secrets` mit Baseline `.secrets.baseline`
- pre-commit-Hook (`language: pygrep`), der Home-Pfade blockiert:
  `/Users/`, `/home/<name>` (außer `/home/vscode`), `C:\\Users\\`

### 7. Einstiegspunkt `make check`

Ein Befehl, der alle Gates in dieser Reihenfolge ausführt und beim ersten
Fehler mit Exit ≠ 0 abbricht:
`ruff check` → `ruff format --check` → `mypy` → `lint-imports` →
`xenon` → `bandit` → `deptry` → `detect-secrets` → `pytest` (mit
Coverage) → `diff-cover` (nur wenn `origin/main` existiert)

### 8. Git-Hooks (`.pre-commit-config.yaml`)

- `pre-commit`: ruff, ruff-format, Home-Pfad-Check, detect-secrets
- `pre-push`: `make check`
- Alle Hooks lokal (`language: system` oder `pygrep`), damit sie hinter der
  Firewall ohne Zusatzdownloads laufen

### 9. CI (`.github/workflows/`)

- `ci.yml` bei PR und Push auf `main`: `uv sync --locked`, dann
  `make check` (mit `fetch-depth: 0` für diff-cover)
- `nightly.yml`: täglich, Tests mit Marker `live`
- `dependabot.yml`: Updates für Python-Abhängigkeiten und GitHub Actions,
  wöchentlich

### 10. Platzhalter

- `src/regradar/core/domain/health.py` mit einer trivialen typisierten Funktion
  und Test, damit alle Gates laufen. Wird in T01 ersetzt.

## Akzeptanzkriterien

- [x] `uv sync` und `make check` laufen grün
- [x] Ein absichtlich eingebauter Verstoß pro Gate (temporär, nicht
      committen) lässt `make check` fehlschlagen
- [x] `git push` mit rotem `make check` wird vom pre-push-Hook blockiert
- [x] Commit mit `/Users/test` in einer Datei wird blockiert
- [x] CI-Workflow läuft grün
