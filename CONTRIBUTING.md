# Contributing to benchmarks

Thanks for contributing.

## Scope

This repository validates API parity and runs framework benchmarks. Keep changes focused on one of these areas:

- parity contract (`test/fixtures/parity`)
- parity runner (`cmd/parity-test`)
- benchmark orchestration (`scripts`, `Makefile`, `docker-compose.yml`)
- docs (`docs/`, `README.md`, `METHODOLOGY.md`)

## Prerequisites

- Go 1.25.7+
- Docker + Docker Compose (for local service runs)
- GNU Make

## Local validation

Run these before opening a PR:

```bash
go test ./...
make test-coverage
TARGET=http://localhost:3001 bash scripts/parity-check.sh
```

For patch coverage against `origin/main`:

```bash
make test-patch-coverage
```

If you changed scripts, also run shell linting if available:

```bash
shellcheck scripts/*.sh
```

If you changed benchmark artifacts or report generation, also run schema validation:

```bash
make benchmark-schema-validate
```

## Pull request process

1. Create a branch from `main`.
2. Keep changes atomic and add/update tests when behavior changes.
3. Run local validation commands.
4. Fill out `.github/pull_request_template.md`.
5. Link relevant issues with `Resolves #<number>`.

## Contract rules

- Do not benchmark a framework before parity passes for that target.
- Do not change matcher semantics (`@any_number`, `@is_iso8601`) without updating fixtures and design docs.
- Keep fixture files endpoint-scoped (`users-*`, `health`) instead of creating a single large fixture file.

## Commit style

Use Conventional Commits when possible:

- `feat:` new functionality
- `fix:` bug fix
- `docs:` documentation only
- `test:` tests only
- `chore:` tooling/build/CI
