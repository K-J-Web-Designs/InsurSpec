# Software Engineering & Anti-Slop Constitution

> **Status**: Active  
> **Authority**: Immutable baseline for specification, architectural planning, code implementation, and agent execution governance across all insurance engineering domains.  
> **Conformance**: Requirements use RFC 2119 normative terms (`MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, `MAY`).

---

## Article I: Anti-Slop Safeguards & Code Cleanliness

### 1.1 Complete Implementation Only
- Agents **MUST NOT** emit placeholder implementations, stubs, stubbed endpoints, or simulated logic in production paths unless explicitly tasked with a mock/scaffolding step.
- Agents **MUST NOT** use truncating ellipses (`// ...existing code...`, `/* rest of file */`). Every file write or targeted edit **MUST** be complete, syntax-valid, and preserve existing functionality and comments.
- Code **MUST NOT** include orphaned `TODO`, `FIXME`, or `TBD` markers introduced during implementation turns. Any unfinished edge case **MUST** be raised to the user or tracked as an explicit blocker.

### 1.2 Zero-Bloat & Anti-Hallucination
- Agents **MUST NOT** add new third-party dependencies if the capability is available in the language standard library or already present in project dependencies.
- Every new package addition **MUST** be explicitly justified in the Technical Plan with security posture, maintenance status, and bundle/runtime impact.
- Agents **MUST NOT** introduce speculative abstractions, generic plugin architectures, or design patterns beyond the immediate requirements (Strict adherence to YAGNI and DRY).

### 1.3 Comment Dignity & Documentation
- Agents **MUST NOT** generate decorative, redundant, or tautological comments (e.g., `// Sets name` above `setName()`).
- Comments **MUST** explain *why* non-obvious logic, edge-case compensation, invariant enforcement, or performance optimizations exist.
- Agents **MUST** maintain docstrings and public API signatures according to the project's canonical documentation guidelines.

---

## Article II: Architecture, State & Concurrency

### 2.1 Codebase Discovery First
- Before creating a new helper, type, utility, or component, the agent **MUST** inspect the existing codebase to identify and reuse canonical patterns and shared modules.
- Agents **MUST NOT** duplicate existing logic under new names or create parallel implementations of established repository conventions.

### 2.2 Error Handling & Resilience
- Agents **MUST NOT** swallow errors silently (`catch (e) {}`, `except Exception: pass`, or unlogged fallbacks).
- Errors **MUST** be handled explicitly: fail fast, enrich with diagnostic context, log with standard loggers, or bubble up to designated domain boundaries.
- Fallback paths **MUST NOT** mask failure modes from telemetry, health checks, or unit test runners.

### 2.3 Simplicity & Locality of Behavior
- Prefer simple, readable, and composable functions over deeply nested inheritance chains or fragmented micro-abstractions.
- Keep state local whenever possible. Minimize global mutable state and hidden side-effects.

---

## Article III: Focused, High-Value Testing (Anti-Test Bloat)

### 3.1 Proportionate Testing & Zero "Vanity Tests"
- Agents **MUST NOT** generate "vanity tests" purely to inflate coverage metrics.
- Agents **MUST NOT** write unit tests for:
  1. Trivial getters, setters, or standard class constructors.
  2. Pure Data Transfer Objects (DTOs), types, or simple data schemas lacking custom logic.
  3. Third-party library internals or framework wiring (e.g., asserting that React renders a native `<div>` or that an ORM maps a field).
  4. Pass-through functions that simply delegate directly to an underlying library without transformation.

### 3.2 The Rule of the "Essential Triad"
Instead of generating dozens of permutations, unit test suites for a given unit **SHOULD** be limited to the **Essential Triad**:
1. **The Happy Path**: The primary successful flow verifying expected output against canonical input.
2. **The Key Boundary / Edge Case**: The most realistic, high-risk boundary (e.g., empty collection, off-by-one limit, malformed payload).
3. **The Expected Failure**: The core error path asserting that invalid input or downstream failure rejects/throws cleanly with the correct diagnostic error.

### 3.3 Consolidate with Table-Driven / Parameterized Tests
- Agents **MUST NOT** write multiple copy-pasted test functions differing only by input values.
- Where multiple input cases must be evaluated, the agent **MUST** use parameterized or table-driven tests (e.g., `test.each`, `@pytest.mark.parametrize`) to keep the test suite concise and readable.

### 3.4 Test Public Behaviors, Not Private Implementation
- Tests **MUST** verify behavior through public APIs and public contracts.
- Tests **MUST NOT** spy on, assert against, or mock internal private methods or transient internal variables. Tests should not break when refactoring internal implementation as long as the external contract holds.

### 3.5 Real Assertions & Mock Discipline
- Tests **MUST NOT** pass vacuous assertions (e.g., asserting variable truthiness when asserting exact values is feasible).
- Mocks **MUST** be reserved exclusively for boundaries that are slow, nondeterministic, or out-of-process (network calls, clocks, disk I/O, database connections). The agent **MUST NOT** mock the internal business logic under test.

---

## Article IV: Data Preservation & Non-Destructive Operations

### 4.1 Zero-Destruction Schema Migrations
- Agents **MUST NOT** drop tables, collections, columns, fields, or indexes that contain existing production or development data.
- All schema modifications **MUST** follow non-destructive **Expand-Contract (additive)** migration patterns:
  1. Add new fields/tables as optional or with safe defaults.
  2. Backfill existing records safely in batches.
  3. Deprecate rather than drop legacy fields until all clients and versions migrate.
- Destructive reset commands (`db:reset`, `drop_database`, `DELETE FROM table`, TRUNCATE, or overwriting seed scripts) **MUST NOT** run without explicit, unambiguous approval from the human operator.

### 4.2 Data Mutation & Soft Deletes
- Application writes **MUST** use idempotent upserts or versioned mutations to prevent accidental overwrites during race conditions.
- Deletions of core user entities (documents, profiles, items, transactions) **SHOULD** implement soft deletion (e.g., `is_deleted: true`, `deleted_at: timestamp`) rather than hard deletes, ensuring data recovery is possible.

---

## Article V: Universal Cross-Device Synchronization & State Integrity

### 5.1 Account-Bound State (No Local-Only Silos)
- All user-generated content, app settings, operational records, and user preferences **MUST** be scoped to the authenticated user account (`userId`) and persisted to a centralized, cloud-backed datastore.
- Agents **MUST NOT** store primary application state exclusively in device-isolated local storage (such as un-synced `localStorage`, isolated local SQLite, raw device files, or `SharedPreferences`) without an automated cloud sync mechanism.

### 5.2 Automatic Multi-Device Synchronization
- Any mutation made on one client instance (e.g., laptop/desktop) **MUST** automatically propagate and reflect on all other instances (e.g., phone, tablet, secondary browser) logged into the same account.
- Applications **MUST** implement either:
  1. **Real-time subscriptions / Push** (e.g., WebSockets, Firestore listeners, Supabase Realtime, server-sent events).
  2. **Reconciliation on App Lifecycle Events**: Automatically pull fresh remote state on app launch, tab focus, network reconnection, and foregrounding.

### 5.3 Offline-First & Deterministic Conflict Resolution
- Local caching is encouraged for offline resilience, but local storage **MUST** be treated as a cache of the canonical cloud state.
- In the event of conflicting edits across devices, the system **MUST** resolve conflicts deterministically using clear strategies (e.g., Last-Write-Wins based on synchronized UTC timestamps, conflict-free replicated data types [CRDTs], or field-level merges). No device may silently overwrite newer cloud data with stale local cache.

---

## Article VI: Security, Secrets & Safe Operations

### 6.1 Secrets & Sensitive Data
- Agents **MUST NOT** commit, log, or hardcode credentials, API tokens, private keys, or test credentials that mirror production values.
- Configuration **MUST** leverage environment variables, secret managers, or standard configuration manifests.

### 6.2 Safe Terminal & Execution Boundaries
- Commands that delete files recursively (`rm -rf`), wipe directories, or modify external cloud resources **MUST NOT** run without prior explicit plan disclosure.
- Agents **MUST NOT** disable security controls, CORS policies, authentication middleware, or TLS verification as a debugging shortcut.

---

## Article VII: The Ambiguity & Clarification Gate

### 7.1 Prohibition on Hallucinated Assumptions
- Agents **MUST NOT** guess or invent unstated business rules, data models, auth tiers, UX workflows, or destructive edge-case behaviors when specifications are incomplete or contradictory.
- Assuming an unspecified requirement is considered a critical defect if the wrong guess causes throwaway code, schema migration issues, or security exposures.

### 7.2 Clarification Triggers (Stop and Ask)
The agent **MUST** pause execution, formulate concise options, and ask the user for clarification before writing code when:
1. **Architectural Forks**: Two mutually exclusive, equally valid design choices exist (e.g., relational table vs. document store, server-rendered vs. client-rendered).
2. **Missing Acceptance Criteria**: The user requests a high-level outcome without defining error semantics, permissions, or boundaries.
3. **Destructive or Irreversible Actions**: The task requires modifying existing database schemas, breaking public API contracts, or replacing existing core services.
4. **Contradictory Directives**: A user instruction conflicts with the codebase conventions or this constitution.

### 7.3 Clarification Format
When requesting clarification, the agent **MUST**:
- State the ambiguity in 1–2 plain sentences.
- Present the recommended path first with trade-offs.
- Provide 2–3 concrete, actionable alternatives (e.g., via multiple-choice or short bullets) so the user can unblock the agent in one turn.

---

## Article VIII: Execution Loop Limits & Token Economy

### 8.1 The 5-Strike Circuit Breaker
- **Max Retry Rule**: An agent **MUST NOT** attempt the same failed operation, command, or failing test fix more than **3 to 5 iterations** within a continuous loop.
- If an operation fails 3 consecutive times with similar errors, the agent **MUST** stop, step back, and re-evaluate the diagnosis rather than trying cosmetic variations.
- If the issue cannot be resolved on the **5th attempt**, the agent **MUST immediately halt**, preserve the current workspace state, and alert the user with:
  1. What was attempted.
  2. The exact root-cause failure log or diagnostic error.
  3. Why the automated attempts stalled.
  4. 2–3 recommended options for human intervention.

### 8.2 Token Budget & Context Preservation
- Agents **MUST NOT** pipe unbounded log streams, raw minified bundles, or large build outputs (e.g., >100 lines) directly into the conversation context. Use targeted grep, tail, line-range slicing, or summary scripts.
- Agents **MUST NOT** re-read entire monolithic files repeatedly when inspecting small segments.
- Avoid multi-turn "ping-pong" loops for deterministic errors (e.g., import missing). Bundle lint/type-check inspection so fixes occur in batch rather than one error per turn.

---

## Article IX: Specification & Planning Protocol (The Spec Gate)

### 9.1 Plan-Before-Code
- For any change involving more than a single trivial bug fix, the agent **MUST** formulate a structured Technical Specification (`/specify`) and Architecture Plan (`/plan`) before modifying code.

### 9.2 Mandatory Constitution Check
Every implementation plan generated by an agent **MUST** include the following verification block:

```markdown
## Constitution Check
- [ ] No stubs, placeholders, or empty catch blocks (Article I).
- [ ] No unnecessary third-party dependencies introduced (Article I).
- [ ] Existing project utilities and conventions reused (Article II).
- [ ] Tests are focused: zero vanity tests, essential triad respected, parameterized where possible (Article III).
- [ ] Existing data protected: zero destructive resets, non-destructive schema migrations only (Article IV).
- [ ] Cross-device sync guaranteed: state is user-scoped, cloud-backed, and auto-syncing across all client instances (Article V).
- [ ] Secrets and credential security respected (Article VI).
- [ ] All requirements clarified; zero unverified business assumptions (Article VII).
- [ ] Execution loop budget and token-efficient test runners identified (Article VIII).
- [ ] Backstage catalog entity and TechDocs synchronized (Article X).
```

If any check fails, the plan **MUST** be refactored before execution begins.

---

## Article X: Mandatory Backstage.io Cataloging & TechDocs Registration

### 10.1 Service & API Entity Registration
- Every newly created or modified service repository **MUST** maintain a valid `catalog-info.yaml` at its root conforming to the enterprise Backstage.io schema.
- The descriptor **MUST** declare: `Component` entity metadata, ownership (`owner`), parent system (`system`), domain (`domain`), exposed APIs (`providesApis`), and consumed dependencies (`consumesApis`).

### 10.2 Technical Documentation (TechDocs) Synchronization
- Every service repository **MUST** maintain a `mkdocs.yml` and `/docs` directory.
- Any architectural change, C4 diagram update, or API modification **MUST** update the corresponding TechDocs markdown documentation in the same pull request.
