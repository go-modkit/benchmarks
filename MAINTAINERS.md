# Maintainers

This document outlines the maintainership roles, triage expectations, and response windows for the `benchmarks` repository.

## Roles

- **Lead Maintainers**: Responsible for the overall direction, architecture, and final approval of major changes.
- **Maintainers**: Responsible for reviewing pull requests, triaging issues, and maintaining specific components (e.g., parity runner, benchmark scripts).
- **Triage**: Responsible for initial issue screening, labeling, and routing questions to [Discussions](https://github.com/go-modkit/benchmarks/discussions).

## Triage Expectations

We aim to provide timely feedback on community contributions while balancing other project priorities.

| Activity | Initial Response Window | Goal |
|----------|-------------------------|------|
| **New Issues** | 2-3 business days | Acknowledge, label, and request missing info. |
| **Pull Requests** | 3-5 business days | Provide initial review or feedback. |
| **Discussions** | Best effort | Community-driven; maintainers participate as time permits. |

*Note: Response windows are targets, not guarantees. We appreciate your patience.*

## Escalation Paths

### Security Vulnerabilities
Do not report security vulnerabilities via public issues. Follow the [Security Policy](SECURITY.md) for private disclosure.

### Urgent Issues
For critical regressions or build failures impacting the main branch, please mention a maintainer in the relevant issue or PR.

## Governance

Decisions are made through consensus among maintainers. For major architectural changes, a design document (RFC) should be submitted to `docs/design/` for review.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the technical contribution process.
