.PHONY: benchmark benchmark-modkit benchmark-nestjs benchmark-baseline benchmark-wire benchmark-fx benchmark-do report test parity-check parity-check-modkit parity-check-nestjs benchmark-fingerprint-check benchmark-limits-check

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
	python3 scripts/generate-report.py

test:
	go test ./...

parity-check:
	TARGET="$(PARITY_TARGET)" bash scripts/parity-check.sh

parity-check-modkit:
	TARGET=http://localhost:3001 bash scripts/parity-check.sh

parity-check-nestjs:
	TARGET=http://localhost:3002 bash scripts/parity-check.sh

benchmark-fingerprint-check:
	python3 scripts/environment-manifest.py check-fingerprint --file results/latest/environment.fingerprint.json

benchmark-limits-check:
	python3 scripts/environment-manifest.py check-limits --compose docker-compose.yml
