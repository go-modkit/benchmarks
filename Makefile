SHELL := /bin/sh
PYTHON ?= python3
GO ?= go

.PHONY: benchmark benchmark-modkit benchmark-nestjs benchmark-baseline benchmark-wire benchmark-fx benchmark-do report test parity-check parity-check-modkit parity-check-nestjs benchmark-fingerprint-check benchmark-limits-check benchmark-manifest-check benchmark-raw-schema-check benchmark-summary-schema-check benchmark-schema-validate benchmark-stats-check benchmark-variance-check benchmark-benchstat-check ci-benchmark-quality-check

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
	$(GO) test ./...

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
