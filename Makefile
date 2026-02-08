SHELL := /bin/sh
PYTHON ?= python3
GO ?= go
PYTEST ?= pytest
BATS ?= bats

ifneq ("$(wildcard .venv/bin/python)","")
PYTHON := .venv/bin/python
endif

ifneq ("$(wildcard .venv/bin/pytest)","")
PYTEST := .venv/bin/pytest
endif

GOPATH ?= $(shell $(GO) env GOPATH)
GO_PATCH_COVER ?= $(GOPATH)/bin/go-patch-cover
MODULES = $(shell find . -type f -name "go.mod" -not -path "*/.*/*" -not -path "*/vendor/*" -exec dirname {} \;)

.PHONY: benchmark benchmark-modkit benchmark-nestjs benchmark-baseline benchmark-wire benchmark-fx benchmark-do report test test-go test-python test-shell test-scripts test-coverage test-coverage-go test-coverage-python test-patch-coverage tools setup-dev-env setup-dev-env-ci setup-dev-env-ci-scripts parity-check parity-check-modkit parity-check-nestjs benchmark-fingerprint-check benchmark-limits-check benchmark-manifest-check benchmark-raw-schema-check benchmark-summary-schema-check benchmark-schema-validate benchmark-stats-check benchmark-variance-check benchmark-benchstat-check ci-benchmark-quality-check workflow-concurrency-check workflow-budget-check workflow-inputs-check todo-debt-check report-disclaimer-check methodology-changelog-check publication-sync-check

benchmark:
	bash scripts/run-all.sh

benchmark-modkit:
	bash scripts/run-single.sh modkit

benchmark-nestjs:
	bash scripts/run-single.sh nestjs

benchmark-baseline:
	bash scripts/run-single.sh baseline

benchmark-wire:
	bash scripts/run-single.sh wire

benchmark-fx:
	bash scripts/run-single.sh fx

benchmark-do:
	bash scripts/run-single.sh do

report:
	$(PYTHON) scripts/generate-report.py

test:
	$(MAKE) test-go
	$(MAKE) test-scripts

test-go:
	$(GO) test ./...

test-python:
	@if ! command -v $(PYTEST) >/dev/null 2>&1; then \
		echo "pytest not found; install with: $(PYTHON) -m pip install pytest pytest-cov"; \
		exit 1; \
	fi
	$(PYTEST) tests/unit

test-shell:
	@if ! command -v $(BATS) >/dev/null 2>&1; then \
		echo "bats not found; install bats-core before running shell tests"; \
		exit 1; \
	fi
	$(BATS) tests/integration

test-scripts:
	$(MAKE) test-python
	$(MAKE) test-shell

test-coverage:
	$(MAKE) test-coverage-go

test-coverage-go:
	@mkdir -p .coverage
	@echo "mode: atomic" > .coverage/coverage.out
	@for mod in $(MODULES); do \
		echo "Testing coverage for module: $$mod"; \
		(cd $$mod && $(GO) test -coverprofile=profile.out -covermode=atomic ./...) || exit 1; \
		if [ -f $$mod/profile.out ]; then \
			tail -n +2 $$mod/profile.out >> .coverage/coverage.out; \
			rm $$mod/profile.out; \
		fi; \
		done
	@printf "\nTotal Coverage:\n"
	@$(GO) tool cover -func=.coverage/coverage.out | grep "total:"

test-coverage-python:
	@if ! command -v $(PYTEST) >/dev/null 2>&1; then \
		echo "pytest not found; install with: $(PYTHON) -m pip install pytest pytest-cov"; \
		exit 1; \
	fi
	$(PYTEST) tests/unit --cov=scripts --cov-report=term-missing

test-patch-coverage: tools test-coverage
	@echo "Comparing against origin/main..."
	@git diff -U0 --no-color origin/main...HEAD > .coverage/diff.patch
	@$(GO_PATCH_COVER) .coverage/coverage.out .coverage/diff.patch > .coverage/patch_coverage.out
	@echo "Patch Coverage Report:"
	@cat .coverage/patch_coverage.out

tools:
	@echo "Installing development tools..."
	@$(GO) install github.com/seriousben/go-patch-cover/cmd/go-patch-cover@latest
	@echo "Done: go-patch-cover installed"

setup-dev-env:
	bash scripts/setup-dev-env.sh

setup-dev-env-ci:
	bash scripts/setup-dev-env.sh --ci --subset core,python-test,go-tools

setup-dev-env-ci-scripts:
	bash scripts/setup-dev-env.sh --ci --subset core,python-test,shell-test,benchmark-tools

parity-check:
	TARGET="$(PARITY_TARGET)" bash scripts/parity-check.sh

parity-check-modkit:
	TARGET=http://localhost:3001 bash scripts/parity-check.sh

parity-check-nestjs:
	TARGET=http://localhost:3002 bash scripts/parity-check.sh

benchmark-fingerprint-check:
	$(PYTHON) scripts/environment-manifest.py check-fingerprint --file results/latest/environment.fingerprint.json

benchmark-limits-check:
	$(PYTHON) scripts/environment-manifest.py check-limits --compose docker-compose.yml

benchmark-manifest-check:
	$(PYTHON) scripts/environment-manifest.py check-manifest --file results/latest/environment.manifest.json

benchmark-raw-schema-check:
	$(PYTHON) scripts/validate-result-schemas.py raw-check

benchmark-summary-schema-check:
	$(PYTHON) scripts/validate-result-schemas.py summary-check

benchmark-schema-validate:
	$(MAKE) benchmark-raw-schema-check
	$(MAKE) benchmark-summary-schema-check

benchmark-stats-check:
	$(PYTHON) scripts/benchmark-quality-check.py stats-check

benchmark-variance-check:
	$(PYTHON) scripts/benchmark-quality-check.py variance-check

benchmark-benchstat-check:
	$(PYTHON) scripts/benchmark-quality-check.py benchstat-check

ci-benchmark-quality-check:
	$(PYTHON) scripts/benchmark-quality-check.py ci-check

report-disclaimer-check:
	$(PYTHON) scripts/publication-policy-check.py report-disclaimer-check

methodology-changelog-check:
	$(PYTHON) scripts/publication-policy-check.py methodology-changelog-check

publication-sync-check:
	$(PYTHON) scripts/publication-policy-check.py publication-sync-check

workflow-concurrency-check:
	$(PYTHON) scripts/workflow-policy-check.py concurrency-check

workflow-budget-check:
	$(PYTHON) scripts/workflow-policy-check.py budget-check

workflow-inputs-check:
	$(PYTHON) scripts/workflow-policy-check.py inputs-check

todo-debt-check:
	$(PYTHON) scripts/todo-debt-check.py
