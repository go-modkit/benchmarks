# Design 002: API Parity Contract Suite

## 1. Goal
Ensure **functional equivalence** across all benchmarked implementations (`modkit`, `nestjs`, `wire`, `fx`, `do`, `baseline`) before measuring performance.

**Why:**
- Performance comparisons are invalid if implementations do different work (e.g., one skips validation, another returns different error shapes).
- Modkit's value proposition is "NestJS architecture in Go" — strict parity proves this claim.

## 2. Scope
The parity contract covers:
1. **Endpoint Semantics**: Status codes, headers, and body structures for all success/error cases.
2. **Data Model**: Identical JSON serialization for `User` entities (timestamps, ID formats).
3. **Error Handling**: RFC 7807 (Problem Details) compliance for validation errors across Go and Node.js.
4. **Seed State**: A deterministic initial database state for consistent read benchmarks.

## 3. Architecture

### 3.1. Golden Fixtures (`test/fixtures/parity/`)
We define the contract using a **declarative JSON-based format**. This allows the test harness to be language-agnostic (though implemented in Go) and easily extensible.

**Directory Structure:**
```
test/fixtures/parity/
├── seed.json           # Initial DB state (users to insert before tests)
├── scenarios/
│   ├── health.json     # Health check behavior
│   ├── users-create.json
│   ├── users-read.json
│   ├── users-update.json
│   └── users-delete.json
└── schemas/            # JSON Schemas for validation (if strict equality fails)
    └── error.json
```

**Scenario Format (`users-create.json`):**
```json
[
  {
    "name": "Create valid user",
    "request": {
      "method": "POST",
      "path": "/users",
      "headers": { "Content-Type": "application/json" },
      "body": {
        "name": "Alice",
        "email": "alice@example.com"
      }
    },
    "response": {
      "status": 201,
      "headers": { "Location": "/users/\\d+" },  // Regex match support
      "body": {
        "id": "@any_number",                      // Fuzzy match
        "name": "Alice",
        "email": "alice@example.com",
        "createdAt": "@is_iso8601"
      }
    }
  },
  {
    "name": "Create invalid user (missing email)",
    "request": {
      "method": "POST",
      "path": "/users",
      "body": { "name": "Bob" }
    },
    "response": {
      "status": 400,
      "body": {
        "type": "https://modkit.io/probs/validation-error",
        "title": "Validation Error",
        "detail": "email is required"             // Exact match required
      }
    }
  }
]
```

### 3.2. Parity Harness (`cmd/parity-test/`)
A standalone Go CLI tool that acts as the "referee".

**Responsibilities:**
1. **Target Agnostic**: Accepts a base URL (`http://localhost:3000`) target.
2. **Reset Strategy**: Calls a dedicated `POST /debug/reset` (only enabled in test mode) or relies on container restart to clear DB state.
3. **Seeder**: POSTs the `seed.json` data to the target app before running read scenarios.
4. **Executor**: Iterates over `scenarios/*.json`, executing requests sequentially.
5. **Asserter**:
   - Strict equality for status codes.
   - JSON deep equality for bodies (with support for `@matchers`).
   - Header presence/value checks.

**Usage:**
```bash
# Run against local modkit app
go run ./cmd/parity-test -target http://localhost:3001 -fixtures ./test/fixtures/parity

# Run against dockerized nestjs
go run ./cmd/parity-test -target http://localhost:3002
```

### 3.3. Integration with Benchmarks
The harness runs as a **pre-flight gate** in the benchmark pipeline:
1. Start framework container (`docker-compose up -d modkit`).
2. Wait for `/health`.
3. Run `parity-test` against it.
4. If pass -> Proceed to `wrk` benchmark.
5. If fail -> Abort and report parity violation.

## 4. Key Decisions & Constraints

### 4.1. SQLite Auto-Increment Parity
**Challenge:** Go `database/sql` vs NestJS TypeORM/Prisma might handle ID generation or return types differently (int vs string).
**Decision:** All APIs MUST return numeric IDs as JSON numbers.
**Enforcement:** The harness will fail if `id: "1"` (string) is returned instead of `id: 1` (number).

### 4.2. Timestamp Precision
**Challenge:** Go `time.Time` (RFC3339Nano) vs JS `Date.toISOString()` (milliseconds).
**Decision:** All APIs MUST normalize to RFC3339 with millisecond precision (e.g., `2024-01-01T00:00:00.000Z`).
**Enforcement:** Parity tests will assert ISO format; deep equality on exact times is skipped in favor of format validation.

### 4.3. Error Shape (Problem Details)
**Challenge:** NestJS default errors vs modkit errors.
**Decision:** Both implementations MUST standardize on a minimal RFC 7807 subset:
```json
{
  "type": "string",
  "title": "string",
  "status": number,
  "detail": "string",
  "instance": "string" (optional)
}
```
**Impact:** Requires adding an Exception Filter in NestJS and a custom ErrorEncoder in modkit/Go apps.

### 4.4. Seeding Strategy
**Challenge:** Benchmarks need a pre-filled DB (e.g., 10k users) for read tests.
**Decision:**
- **Parity Tests:** Use the harness to POST `seed.json` (small dataset, ~10 records).
- **Load Benchmarks:** Use a separate `POST /debug/seed` endpoint or a dedicated seeder script to bulk-insert 10k records before `wrk` starts.
- **Why:** Keeps the parity harness fast and focused on correctness, while load benchmarks manage their own scale needs.

## 5. Implementation Plan

1. **Step 1 (Task #8):** Create `test/fixtures/parity/*.json` defining the "Golden Contract".
2. **Step 2 (Task #9):** Build `cmd/parity-test` runner in Go.
3. **Step 3 (Modkit Impl):** Update `apps/modkit` to pass the harness (implement error formatting, ISO timestamps).
4. **Step 4 (NestJS Impl):** Update `apps/nestjs` to pass the harness (add Exception Filter, JSON serialization tweaks).
5. **Step 5 (Task #10):** Add `make parity-check` target to `Makefile` and CI.
