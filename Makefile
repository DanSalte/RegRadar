.PHONY: check

RUN := uv run --frozen

# Gates run in the order of T00; make stops at the first failing one.
check:
	$(RUN) ruff check
	$(RUN) ruff format --check
	$(RUN) mypy
	$(RUN) lint-imports
	$(RUN) xenon --max-absolute B --max-average A src
	$(RUN) bandit -q -r src
	$(RUN) deptry .
	git ls-files -z | xargs -0 $(RUN) detect-secrets-hook \
		--baseline .secrets.baseline
	$(RUN) pytest --cov --cov-report=term-missing --cov-report=xml
	@if git rev-parse --verify -q origin/main >/dev/null; then \
		$(RUN) diff-cover coverage.xml --compare-branch=origin/main \
			--fail-under=90; \
	else \
		echo "diff-cover skipped: origin/main not found"; \
	fi
