# Standalone agent handoff specification

This file contains the complete execution specification. All referenced milestone specifications are included below; external milestone files are editable source copies. When given only this file, read the included sections directly. M0 contracts take precedence over conflicting details. M9 names the long-tail capability packs from the original design, not a prerequisite for M1–M8.

# CTF Workbench — Agent Execution Specification

## 0. Start here

### 0.1 Purpose and execution instruction

This is an implementation specification, not a shell executable. Give this file to a coding agent and instruct it to implement the next uncompleted milestone. Read this file first, then the referenced milestone file. The original `CTF Workbench Human-Centric Design Doc.md` supplies product intent; this specification supplies implementation order and concrete defaults. Do not interpret writing this specification as permission to start implementation.

Suggested agent prompt:

> Read EXECUTION_PLAN.md and its referenced specifications. Inspect the actual repository and task ledger. Implement the earliest ready milestone, delegating independent tasks to subagents with exclusive file ownership. Follow the contracts and acceptance criteria. Deliver working integrated code, run the relevant checks, and update the ledger with evidence. Do not substitute mock screens or disconnected stubs for functional deliverables. Stop at the requested milestone boundary; report blockers honestly.

### 0.2 Specification index

1. [M0: foundation and contracts](docs/execution/01-foundation.md).
2. [M1–M2: workbench, execution, and viewers](docs/execution/02-workbench.md).
3. [M3–M5: sidekick, verification, and delegation](docs/execution/03-agents.md).
4. [M6–M8: hunts, platforms, collaboration, and evaluation](docs/execution/04-expansion.md).

### 0.3 Fixed implementation decisions

- Build a local-first single-user application first; preserve competition and actor IDs for later teams.
- Host target: Windows with Docker Desktop/WSL2; Linux development must also work. Challenge tools run in Linux containers.
- Backend: Python, FastAPI, Pydantic, SQLAlchemy, Alembic. Start with SQLite WAL and foreign keys enabled. Add PostgreSQL at M7.
- Frontend: React, TypeScript, Vite, Tailwind; use generated OpenAPI types, TanStack Query for server state, and feature-local state for selection/layout.
- Python layout: `src/ctf_workbench/{domain,db,services,api,tools,jobs,sandbox,agents,mcp,integrations}`. Frontend: `apps/web/src/{app,shared,features}`.
- Artifact blobs live outside Git under a configured data root. Challenge working directories are separate Git repositories under that root.
- Use a database-backed worker queue initially. Do not introduce Redis, Celery, Kubernetes, hosted storage, or hosted editors before demonstrated need.
- code-server is the initial editor candidate; prove proxy and security requirements in M0 before depending on it.
- opencode owns the agent loop. The application owns authorization, scope, context, budget accounting, evidence, and job lifecycle.
- Pin tested dependency versions and image digests during implementation. Consult official documentation for changing external APIs; record the tested versions. Never fabricate endpoint compatibility.

### 0.4 Product invariants

#### 0.4.1 Provenance

Every persisted mutation has an authenticated actor and transactionally appended event. Every tool result records normalized parameters, input hashes, versions, output references, and terminal status. A claim without evidence remains visibly unsupported.

#### 0.4.2 Human authority

Agents create proposals. Accepting a proposal creates a hypothesis; a separate explicit human confirmation changes it to confirmed. Verification proves a declared predicate, not the surrounding interpretation. No agent endpoint can confirm claims, approve flags, or approve its own capabilities.

#### 0.4.3 One tool implementation

UI and MCP invoke the same ToolRunService and typed registry. Neither frontend duplicates algorithms. Service-layer authorization is mandatory even when an API adapter already performed a check.

#### 0.4.4 Isolation

Parsers, notebook code, terminals, agent commands, and unknown binaries execute in the sandbox. Never mount host credentials or Docker sockets into challenge containers. The trusted sandbox manager alone controls Docker. Containers are not a promise of malware-grade isolation; detonation requiring stronger isolation uses the VM feature.

#### 0.4.5 Privacy and offline operation

Manual work remains available without model credentials or internet. External model use requires an enabled event policy and visible context-transfer indication. Do not claim files never leave the machine when selected contents are sent to a model. Platform credentials never enter prompts or general event payloads.

## 1. Agent coordination protocol

### 1.1 Task ledger

#### 1.1.1 Required state

At implementation start create `docs/execution/STATUS.md`. For every atomic task record ID, status (`pending`, `claimed`, `in_progress`, `blocked`, `review`, `done`), owner, dependencies, files, validation evidence, and blocker. Initially no implementation task is done merely because this specification exists.

#### 1.1.2 Resume behavior

Inspect repository changes and existing tests before claiming tasks. Resume unfinished work; do not overwrite uncommitted user changes. A prior done status is evidence to inspect, not a reason to recreate a feature.

### 1.2 Dependency scheduling

M0 precedes M1. M1 precedes M2 and M3; M3 requires the durable execution contract introduced in M1 and hardened in M2. M4 follows M3. M5 follows M4. M6 follows M2 for manual hunt features and M4 for agent-assisted features. M7 follows M6. M8 instrumentation begins at M0; the full interface follows M7. Honor stricter dependencies inside each specification.

### 1.3 Subagent assignment

#### 1.3.1 Required delegation packet

Provide task IDs, goal, relevant contract excerpts, permitted files, forbidden shared files, upstream assumptions, fixtures, acceptance checks, and expected report format. An agent may read any relevant project file but edits only its assigned paths. Reassign ownership explicitly before crossing boundaries.

#### 1.3.2 Integration owner

The coordinating agent exclusively owns migrations, shared Pydantic schemas, generated API types, package manifests, lockfiles, application composition, and the status ledger. Domain subagents propose changes to these files through a handoff; they do not race on them.

#### 1.3.3 Parallel lanes

After contract freeze, separate backend services, tool implementations, frontend features, and integration fixtures. Frontend work may use contract fixtures temporarily, but milestone completion requires real API wiring. Each subagent returns changed paths, implemented behavior, tests executed with results, and unresolved issues.

### 1.4 Definition of done for every atomic task

Implementation exists and is called from its intended entry point; authorization and failure handling match the contract; relevant tests pass; no mock fallback masks unavailable dependencies; schema changes have migrations; user-facing errors suggest a concrete recovery; documentation records any intentional limitation. The coordinator verifies cross-component behavior before marking a milestone done.

### 1.5 Handling uncertainty

Use specified defaults for routine choices. If an upstream API differs, implement a narrow adapter and document the verified contract. If a required dependency is unavailable, finish independent tasks, mark dependent tasks blocked, and report the exact missing prerequisite. Never lower a completion gate to hide a missing integration.

## 2. Global acceptance and delivery

### 2.1 Commands the implementation must provide

Provide documented commands for backend install, frontend install, migrations, API, worker, frontend development, unit tests, integration tests, browser tests, lint, type checks, and production build. Provide a PowerShell launcher and Linux equivalent that check prerequisites, bind locally, print URLs, and shut down owned processes without killing unrelated processes.

### 2.2 Release artifacts

Each milestone delivers runnable source, migrations, lockfiles, fixtures, relevant tests, a short walkthrough, and an updated status ledger. Do not promise a single portable `.exe`: Docker, Linux tool images, and model runtimes are external prerequisites. Packaging an installer is a separate future deliverable.

### 2.3 Integration scenario

Create a challenge, import ciphertext and an image, inspect hashes/bytes, run tools, persist output, attach evidence to a hypothesis, confirm it as a human, write notes, run a solver in the sandbox, restart, and recover the same references. From M3 onward also ask the sidekick, inspect its citations, and accept its proposal. From M6 onward approve a mock-platform submission and inspect its recorded response.

### 2.4 Scope accounting

All broad tool families in the design remain planned, but adapters are implemented in explicit batches in the milestone documents. Mark unavailable capabilities as unavailable with installation/version diagnostics. Do not expose a successful-looking button backed by a placeholder.


---

# M0 — Establish the foundation and freeze shared contracts

## M0.1 Repository and runtime

### M0-01 — Scaffold the application

#### Goal

Create a minimal bootable Python API and React application with a separate worker entry point. No feature code is required to prove the scaffolding.

#### Implementation atomics

##### Python package

Create `pyproject.toml`, `src/ctf_workbench/__init__.py`, `api/main.py`, `jobs/main.py`, and configuration module. Use one validated Settings object for database URL, data root, bind address, session settings, Docker connection, and log level. Reject invalid settings at startup. Keep secrets out of repr/log output.

##### Frontend package

Create `apps/web` with strict TypeScript, Vite, router, error boundary, query client, and health screen. Provide distinct API URL configuration for development and same-origin production. No model SDK belongs in browser code.

##### Developer commands

Create root README and launch scripts. Separate dependency installation from ordinary startup. Commit lockfiles; choose compatible supported versions during implementation and record them. Add ignore rules for data, `.env`, caches, node_modules, and local runtime output.

#### Deliverables and acceptance

API health responds; frontend displays actual API availability; worker starts and exits cleanly. Production frontend builds. Missing settings produce actionable errors. Owner: integrator; dependencies: none.

## M0.2 Persistence and domain model

### M0-02 — Database and migrations

#### Goal

Make persisted application state transactional, restartable, and independently migratable.

#### Implementation atomics

##### Connection behavior

Use SQLAlchemy sessions scoped to requests/jobs. SQLite enables WAL, foreign keys, and a bounded busy timeout. Keep write transactions short. Never hold a database transaction during subprocess execution or network I/O. Alembic owns all schema changes; application startup checks migration compatibility rather than silently rewriting tables.

##### Common fields

Use UUID string IDs, UTC timestamps, and integer revision fields starting at 1 on editable entities. Requests carry expected revision; compare-and-swap updates return 409 on conflict. Pagination uses opaque stable cursors and bounded page sizes (default 50, maximum 200).

##### Initial entities

- `competitions`: id, title, rules_text, assistance_policy_json, flag_pattern, created_at, revision.
- `actors`: id, kind human/tool/agent/system, display_name, disabled_at. Local bootstrap creates one admin human.
- `challenges`: id, competition_id, title, description, category, points nullable, source, external_id nullable, hints_json, scope_json, status open/in_progress/solved/archived, owner_id nullable, parent_meta_id nullable, revision.
- `blobs`: sha256 primary key, size_bytes, storage_key, created_at. Never store a user-supplied path as storage_key.
- `artifacts`: id, challenge_id, blob_sha256, display_name, media_type, kind, origin_event_id, created_at. Use a separate artifact-parent join table for multiple inputs.
- `items`: id, challenge_id, text, kind lead/fact/dead_end, status hypothesis/verified/confirmed/dead_end, author_id, pinned, created_by_event, revision.
- `evidence`: id, challenge_id, item_id nullable, artifact_id nullable, tool_run_id nullable, selector_json, excerpt, predicate_json nullable, rerunnable, created_at.
- `links`: id, competition_id, from_type, from_id, to_type, to_id, relation, created_by_event. Validate endpoint existence and permitted cross-challenge scope in the service.
- `notes`: id, challenge_id, content_json, revision, updated_at; content is an ordered list of cells with stable IDs and kind markdown/python/shell/tool.
- `events`: id, stream_id, seq, ts, actor_id, challenge_id nullable, type, schema_version, payload_json, correlation_id. Unique(stream_id,seq).
- `outbox`: id, event_id, destination, payload_json, available_at, delivered_at nullable, attempts.

##### Forward-compatible references

Add tool_runs/jobs/approvals tables when M0-05 contracts are implemented. Later milestones add feature tables through new migrations; never fake absent runtime data to satisfy a foreign key. Define insertion order for event/entity references in one transaction or use deferrable-compatible patterns verified on SQLite.

#### Deliverables and acceptance

Empty database upgrades to head; fixtures survive close/reopen; invalid foreign keys fail; concurrent stale updates return conflict; state and event either both commit or both roll back. Dependencies: M0-01. Owner: integrator.

### M0-03 — Events and live delivery

#### Goal

Use events for audit and UI updates without making the entire application a custom event-sourced database.

#### Implementation atomics

##### Event append

Implement EventService.append within the caller transaction. Allocate monotonically increasing sequence numbers per stream transactionally, not from wall-clock timestamps. Use challenge ID as stream ID and `global` for competition/system changes. Events cannot be edited through public APIs.

##### Outbox delivery

Insert outbox records with the state mutation. Deliver at least once; consumers deduplicate by event ID. Mark delivered only after acknowledgment. Crashing after send but before acknowledgment may cause duplicate delivery, never duplicate state changes.

##### Browser subscription

Expose authenticated `/api/v1/events?stream_id=&after_seq=` history and `/api/v1/ws/events` live subscription. Authorize stream access. On reconnect replay persisted events after cursor, then live events without a gap. Client deduplicates event IDs. Bounded queues disconnect slow consumers with a resume cursor rather than consuming unlimited memory.

#### Deliverables and acceptance

Two ordered updates appear in another browser session; disconnect/reconnect loses no event; duplicate delivery causes one visible change. Dependencies: M0-02.

## M0.3 Public contracts

### M0-04 — API, errors, references, and authentication

#### Goal

Give parallel feature agents a stable integration surface.

#### Implementation atomics

##### API conventions

All routes begin `/api/v1`. JSON errors have `{error:{code,message,details,request_id}}`. Use 401 unauthenticated, 403 denied, 404 absent or inaccessible resource, 409 revision/state conflict, 413 size limit, 422 invalid inputs, 429 quota, 503 unavailable dependency. Never return raw subprocess exceptions or credentials.

##### Reference schema

Define `ResourceRef={kind,id,challenge_id,version,selector}`. Selector variants include byte range `{start,end_exclusive}`, text `{line_start,line_end,column_start,column_end}`, packet `{packet_number,stream_id}`, image `{x,y,width,height}`, function `{address,analysis_revision}`. Validate ranges against the referenced immutable version; mutable workspace selections first create a snapshot artifact.

##### Local session

Bootstrap a human session through a one-time local token exchanged for HttpOnly SameSite cookies. Require CSRF protection on cookie-authenticated mutations and origin checks on WebSockets. Bind localhost by default. Never put persistent tokens in URLs, browser storage, or logs. Provide session logout/revocation. Agent service credentials use separate scoped authentication and cannot impersonate the local human.

##### Generated clients

Export OpenAPI and generate TypeScript contracts. Keep one HTTP client implementing errors, credentials, request IDs, cancellation, and pagination. Regenerate under integrator ownership when schemas change.

#### Deliverables and acceptance

Unauthorized REST and WebSocket operations fail; stale references return useful errors; frontend renders structured errors; generated contracts match backend. Dependencies: M0-02.

### M0-05 — Tool runs, jobs, and policy

#### Goal

Specify the single execution path before implementing individual tools.

#### Implementation atomics

##### Tool descriptor

Define `ToolDescriptor={name,version,input_schema,output_schema,effects,resource_defaults,capabilities}`. Names are stable dotted identifiers. Effects are a set of read_artifact/write_artifact/execute_code/network/workspace_write/vm_mutation. Tool arguments never choose arbitrary host paths or bypass effect declarations.

##### Invocation and results

`ToolRunRequest={challenge_id,tool_name,tool_version,inputs,parameters,idempotency_key}`. Inputs reference artifacts, never trusted browser filesystem paths. `ToolRunResult={id,status,summary,structured_output,output_artifact_ids,evidence_ids,stdout_ref,stderr_ref,error,timing,versions}`. Status is queued/running/succeeded/failed/cancelled/timed_out. Persist normalized input and parameter hashes before dispatch.

##### Job persistence

Jobs contain id, kind, challenge_id, actor_id, state, payload, attempt, available_at, lease_owner, lease_expires_at, heartbeat_at, cancel_requested_at, result_ref, error. Lease acquisition is atomic. Running jobs require heartbeat; expired leases become retryable only when their effect classification permits retry. Non-idempotent effects enter an uncertain/reconciliation state represented separately from successful completion.

##### Idempotency

Scope keys to actor/challenge/operation. Same key and same request returns the original run; same key with different request returns 409. Cache reuse is separate: tool version, input hashes, normalized parameters, image digest, and relevant analysis revision participate in cache identity.

##### Policy service

`authorize(actor, action, resource, effects, context)` returns allow, deny(reason), or require_approval(action_digest). Evaluate role, competition rules, challenge autonomy, allowed tools, scope, and budget. Enforcement occurs before queueing and again immediately before execution. Changing policy invalidates pending permission assumptions.

##### Approval persistence

Store immutable action digest, requester, authorized human approver, expiration, state pending/approved/rejected/consumed/expired, and policy revision. Approvals authorize the exact action once; changed arguments require a new approval. Agent identities cannot approve.

#### Deliverables and acceptance

Identical idempotent requests create one run; changed payload conflicts; queued work blocked by a later policy change does not execute; approvals cannot be replayed. Dependencies: M0-02, M0-04.

## M0.4 Runtime integration spikes

### M0-06 — Prove sandbox and editor topology

#### Goal

Eliminate host/container networking and filesystem assumptions before M1 builds on them.

#### Implementation atomics

##### Sandbox manager boundary

Implement a trusted manager interface `create/start/stop/exec/stream/copy/snapshot_workspace/destroy`. Only the manager accesses Docker. Use generated container names and validated challenge IDs. Store resolved container identity, image digest, and workspace mount records.

##### Network topology experiment

Prove an authenticated control-plane proxy can reach code-server and its WebSockets without publishing the editor on a public host interface. A service listening on container loopback requires a same-network-namespace connector; alternatively use an isolated internal interface with authenticated ingress and explicitly document that deviation. Do not assume host localhost equals container localhost.

##### Filesystem experiment

Create a file in editor, read it in terminal, create a derived artifact, and prove host-side artifact bytes remain immutable. Verify Windows path handling and permissions. Preserve workspaces across container recreation.

##### Resource and egress experiment

Test CPU/memory/process/output limits; no privileged mode; no host credentials/socket. Start with no egress. Verify any allowlist mechanism blocks direct connections as well as application proxy bypass. A proxy environment variable alone is insufficient. Document DNS and destination-port handling.

#### Deliverables and acceptance

Commit a small reproducible integration test and architecture decision document with tested image/editor versions. Missing Docker produces a clear disabled-feature state. Do not mark the spike passed without actual execution. Dependencies: M0-01, M0-04.

## M0.5 Foundation completion

### M0-07 — Freeze contracts and delegate M1

#### Goal

Permit independent implementation without schema drift.

#### Deliverables

Publish the generated API schema, Python protocol definitions, fixture examples, startup commands, and task ledger. Assign services, tools, frontend, and sandbox lanes with separate paths. Integrator retains migrations and shared contracts.

#### Acceptance

Run build/type checks and the M0 persistence/auth/event tests. Demonstrate the editor topology spike. List any unavailable integrations as blockers. Only then start dependent M1 atoms; independent pure tool work may begin once M0-05 is frozen.


---

# M1 — Manual workbench with complete provenance

## M1 execution contract

Goal: solve a small crypto challenge and a small file-forensics challenge without an agent, preserve the investigation, and reproduce its tool outputs after restarting.

Prerequisite: complete M0 storage, identity, event, policy, and API foundations. All paths below are repository-relative. Task IDs identify independently reviewable units; suffixes identify implementation atomics. Shared schema changes go through the coordinator before parallel work begins.

### Ownership and delegation lanes

| Lane | Owned paths | Inputs required |
| --- | --- | --- |
| Core services | `src/ctf_workbench/services/`, `api/` | M0 contracts |
| Tools | `src/ctf_workbench/tools/` | Tool request/result contracts |
| Execution | `src/ctf_workbench/jobs/`, `sandbox/`, `infra/docker/` | Job and policy contracts |
| Browser | `apps/web/src/features/` | Generated API types and fixtures |

Assign individual subdirectories to concurrent agents. Only the coordinator edits migrations, dependency manifests, generated clients, root routing, and shared application composition. Test directories mirror ownership. An agent must return changed files, task IDs, commands actually run, results, and remaining dependencies.

All HTTP and WebSocket routes below use the `/api/v1` prefix. M0 contracts are authoritative; this file refines behavior without introducing alternate schemas.

### Shared behavior required by every task

#### Transactions and identity

Every mutation uses the authenticated actor from the request context. Never accept an actor or permission assertion from a client payload. Commit mutation, audit event, and dispatch outbox row together. References must resolve within the caller's authorized challenge or competition.

#### Concurrency and errors

Mutable resources carry an integer `revision`. Updates supply `expected_revision`; mismatches return HTTP 409 with current revision and do not overwrite newer content. Use the foundation error envelope. Distinguish validation (422), authorization (403), missing resources (404), conflicts (409), exhausted limits (429), and unavailable capabilities (503).

#### UI completeness

Every panel implements loading, empty, ready, stale, failed, and permission-denied states where applicable. Destructive or long-running operations show their actual state. Buttons must never imply successful persistence before the server acknowledges it. Preserve keyboard focus and provide accessible labels.

## M1-01 — Challenge lifecycle

### Goal and visible behavior

Users create an event, add challenges manually, filter them, claim one, and reopen its last workspace. Challenge metadata is separate from imported file content.

#### M1-01.a — Service and API

Depends on M0. Own `services/challenges.py`, `api/challenges.py` and matching tests.

Implement create/list/get/update/archive operations. Fields: competition ID, title, description Markdown, category, optional points, hints, declared endpoints, owner ID, and status (`open`, `in_progress`, `solved`, `archived`). Trim titles, require 1–200 characters, reject negative points, and bound description size. Endpoint declarations are structured host/port/protocol records; storing one does not grant network access without policy activation.

##### Mutation atomics

- Create a challenge with default status `open`, revision 1, and event `challenge.created`.
- Update only supplied fields, validating ownership and revision.
- Archive without deleting artifacts, history, notes, or evidence.
- Keep human-marked solved status distinguishable from platform-confirmed solve state.

##### Verification and deliverables

Return paginated lists with stable ID tie-breaking. Verify creation, filtered listing, conflict rejection, and archive/reopen behavior. Deliver persisted endpoints and real API integration tests.

#### M1-01.b — Dashboard and header

Own `apps/web/src/features/challenges/`. Render status/category filters, metadata form, and challenge header. Store filters in URL query parameters. Header shows active policy, owner, hints, and declared target. Link each card to `/challenges/:id`; show a recoverable not-found screen for invalid IDs.

##### Acceptance

A new challenge survives a full restart and appears in the same filtered dashboard. Editing its title in two tabs produces a visible conflict instead of losing either edit.

## M1-02 — Immutable artifacts and import

### Goal and visible behavior

Users upload original files and inspect their size, hash, type, provenance, and descendants. Renaming a display label never changes artifact identity.

#### M1-02.a — Streaming ingestion

Depends on M1-01. Own `services/artifacts.py`, `api/artifacts.py`.

Stream uploads into an application-controlled temporary directory while calculating SHA-256 and enforcing configured upload/disk limits. Never allocate the entire upload in memory. Treat the submitted filename as metadata, not a destination path. Atomically promote complete bytes into content-addressed storage and register a challenge-scoped artifact record. Deduplicate physical blobs by hash while retaining separate authorized references.

##### Storage atomics

- Reject partial uploads and clean their temporary files.
- Validate an existing blob's size before reuse; quarantine contradictory metadata.
- Store `sha256`, size, display name, media/type hint, creation event, and parent relationships.
- Represent multiple input parents with artifact edges rather than a single parent column alone.
- Never serve arbitrary filesystem paths supplied by a browser.
- Garbage-collect orphan temporary blobs only after a grace period; retain anything referenced by a committed record.

##### Acceptance

Uploading identical bytes twice does not duplicate storage, and access through one challenge cannot enumerate another challenge's artifact records. Traversal-style filenames remain harmless display strings.

#### M1-02.b — Byte range and download API

Provide metadata lookup, paginated artifact listing, and authenticated content retrieval with byte ranges. Return 416 for invalid ranges; set safe download headers. An artifact reference contains ID and hash; verify both when a caller expects an immutable version. Downloads use the registered blob, never the mutable workspace copy.

#### M1-02.c — Browser and lineage UI

Own `apps/web/src/features/artifacts/`. Display originals and derived outputs with sortable name, size, kind, and origin. Show direct parents and tool-run links in a details panel. Provide explicit download and “copy into workspace” actions. Workspace import copies bytes and records origin; subsequent editing creates new snapshots without modifying the original artifact.

## M1-03 — Board, evidence, and stable references

### Goal and visible behavior

Users track hypotheses, evidence, confirmed facts, and dead ends without losing who asserted what or why.

#### M1-03.a — Item service

Own `services/board.py`, `api/board.py`. Fields: text, kind (`lead`, `fact`, `dead_end`), status (`hypothesis`, `verified`, `confirmed`, `dead_end`), author, pinned, revision, created event. Human-created items default to hypothesis unless the person explicitly confirms them. Confirmation records a human actor and timestamp. Automated verifiers may set verified only through the later verification service.

##### Transition atomics

- Human edits require expected revision.
- Confirmation is a separate explicit action.
- Dead-end action requires a reason and retains earlier evidence.
- Reopening a dead end creates a transition event and returns it to hypothesis.
- Evidence deletion means unlinking with an audit event, not erasing underlying runs.
- Agent proposals added in M3 cannot call privileged transition paths.

#### M1-03.b — Evidence contract

Evidence contains artifact reference or tool-run reference, optional byte range `[start,end)`, optional immutable text line range, excerpt, and interpretation. Validate ranges against the referenced object. Store line references with content hash; line numbers alone are not stable.

Support references shaped as `{kind,id,challenge_id,version,selector}` where selector is typed by kind: bytes, lines, packet, function, or whole object. Serialize references in notes as application links; validate them at resolution time. Unavailable targets show “reference unavailable” without silently substituting a newer object.

##### Acceptance

Selecting bytes 10–20 and adding evidence opens precisely those bytes later, including after the working file changes. A failed evidence transaction does not leave a phantom board event.

#### M1-03.c — Board panel

Own `apps/web/src/features/board/`. Cards show author, status, evidence count, and pinned state. Distinguish “accept as lead” from “confirm” in later inbox integration. Show unsupported claims explicitly. Provide filter, edit, pin, confirm, mark dead end, and open evidence actions.

## M1-04 — Shared tool registry and execution service

### Goal and integration boundary

UI and future MCP clients invoke the same tools with the same validation, policy, execution, and provenance. Frontend code must not implement independent decoding logic.

#### M1-04.a — Registry contract

Own `tools/registry.py` and `tools/contracts.py`. Use the M0 ToolDescriptor exactly; represent execution effects through its effects field and limits through resource_defaults. Keep deterministic/cache eligibility as registry implementation metadata. Register descriptors at startup and reject duplicate names/versions.

Tool invocation and result use M0 ToolRunRequest and ToolRunResult unchanged. Put warnings in structured_output and execution metrics in timing. Binary output is an artifact reference, never an ambiguous string. Text outputs declare encoding.

#### M1-04.b — Tool-run service

Own `services/tool_runs.py`, `api/tools.py`. Persist accepted requests before execution. Canonicalize parameters; capture exact input hashes, tool/container versions, timestamps, actor, and policy decision. Return a job/run reference for execution and expose polling plus events.

##### Implementation atomics

- Route all heavy or untrusted parsing to sandbox workers.
- Allow tiny deterministic transforms through the same recorded job path.
- Separate command arguments from shell strings; tool wrappers never concatenate untrusted shell commands.
- Use explicit shell execution only for user-authored notebook/terminal code.
- Persist failure category and bounded output even when execution fails.
- A retry creates a new attempt linked to the original run.
- Re-running uses original hashes and parameters; unavailable versions require explicit selection of a new version and a new run.

##### Acceptance

Invoke one transform through HTTP and the service interface; both produce equivalent structured results and provenance. Idempotency-key reuse with different content returns 409.

## M1-05 — Core toolbox algorithms

### M1-05.a — Hex, strings, entropy, and hashes

Own `tools/general/`. Read in chunks. Strings returns byte offsets, lengths, encoding, and text for printable ASCII and optional UTF-16LE/BE sequences with configurable minimum length. Define printable ASCII as bytes 0x20–0x7e; terminate runs at other bytes. UTF-16 offsets always refer to original bytes.

##### Algorithm atomics

- Hex view: return offset plus byte arrays, not preformatted HTML.
- Entropy: Shannon entropy in bits/byte using a declared window and stride; include partial final-window size.
- Hashing: SHA-256 by default; optional MD5/SHA-1 for CTF comparison, clearly named.
- Hash identification: return candidate formats from syntax/length, never claim an algorithm was proved.
- Binary diff: return bounded differing intervals; support pagination for large results.

##### Tests

Use known byte fixtures, a UTF-16 string crossing a read boundary, constant bytes with entropy zero, and all byte values with entropy eight. Assert exact offsets and hashes.

### M1-05.b — Encodings and classical ciphers

Own `tools/encodings/`, `tools/ciphers/`. M1 supports Base16/32/64/85, URL and HTML entity decoding, Caesar/ROT-N, Atbash, XOR, and Vigenère with supplied key. Add remaining long-tail tools in later catalog tasks.

##### Exact semantics

- Base decoding is strict by default; optional whitespace removal is an explicit parameter recorded in the run.
- Never silently repair invalid padding; expose repair as a separate requested operation.
- Caesar operates on ASCII letters, preserves case, leaves other characters unchanged, and normalizes shift modulo 26.
- Vigenère advances the key only on ASCII letters; key must contain at least one letter and no nonletters.
- XOR accepts explicit hex key bytes, repeats them cyclically, and returns binary output.
- Decoding text from resulting bytes requires an explicit encoding; invalid UTF-8 remains binary unless replacement mode is requested.

##### Tests and deliverables

Provide golden vectors, inverse-property tests where valid, malformed-input cases, registry descriptors, and UI forms generated from typed parameters with human-readable labels.

### M1-05.c — Paste-anything analyzer

Own `tools/analyzer/`. Accept text with explicit UTF-8/hex interpretation or an artifact. Search candidate transformations breadth-first and deduplicate by output hash plus interpretation. Preserve every candidate's transformation chain.

##### Bounded search defaults

Limit raw input to 1 MiB, depth to 3, evaluated candidates to 256, each output to 8 MiB, cumulative outputs to 32 MiB, expansion ratio to 100, and wall-clock execution to 10 seconds. Configuration may lower limits; increasing them requires the same policy review as other resource changes.

##### Ranking atomics

- Try strict Base encodings, known compression signatures, Caesar shifts, and single-byte XOR.
- Score UTF-8 validity, printable fraction, known file magic, configured flag-pattern match, and versioned language frequency evidence.
- Return component scores and a stable tie-break on recipe then hash.
- Label the score as a heuristic, never a probability.
- Flag regex matches create candidates, not solved status.
- Stop gracefully with `truncated=true` and the reached limit; retain useful partial candidates.

##### UI and acceptance

Show ranked candidates with preview, recipe, warnings, and “continue from this output.” Continuing creates a new recorded run. A Base64→gzip fixture yields the original bytes; a compression bomb terminates within configured limits.

## M1-06 — Hex viewer and selection context

### Goal

Inspect large artifacts without loading them completely and reuse exact selections across tools, board, and notes.

#### M1-06.a — Virtualized viewer

Own `apps/web/src/features/viewers/hex/`. Render 16 bytes per row with offset, hex, and printable text. Request aligned windows through the range API; cache by artifact hash and window. Bound cache size and cancel obsolete requests after navigation. Accept decimal and hexadecimal go-to offsets.

#### M1-06.b — Selection object

Store the M0 ResourceRef with artifact ID, challenge ID, SHA-256 version, and byte selector `{start,end_exclusive}`. Selection can span unloaded windows without fetching the full span; tool invocations pass the reference. Enforce a preview byte cap. Context menu offers copy, decode, add evidence, and send to notebook. Sidekick action appears only when M3 capability is enabled.

##### Acceptance

Opening a multi-gigabyte sparse fixture consumes bounded browser memory; selecting across a window boundary produces correct bytes and offsets.

## M1-07 — Notebook and executable cells

### Goal

Keep explanatory notes and reproducible operations together. Outputs remain associated with the cell revision that produced them.

#### M1-07.a — Document persistence

Own `services/notebooks.py`, `api/notebooks.py`, `apps/web/src/features/notebook/`. Use ordered cells with stable IDs and types `markdown`, `tool`, `python`, `shell`. Persist cell source and revision separately from execution records. Sanitize rendered Markdown; disable raw HTML by default. Debounce saves and show unsaved/conflict states.

#### M1-07.b — Execution behavior

Tool cells use M1-04. Python and shell cells become sandbox jobs with immutable source artifacts, working-directory snapshot reference, and recorded environment version. Initial version uses a fresh process per cell; do not imply shared Python kernel state. Users persist intermediate results as files or artifacts.

##### Output atomics

- Link execution to the exact source revision.
- Mark old outputs stale when source changes.
- Persist stdout/stderr as bounded artifact streams.
- Capture generated files only from declared output directories under configured quotas.
- Cancellation changes execution state without deleting the cell.
- “Add output to board” attaches the run and artifact references.

##### Acceptance

Run, edit, and rerun a cell: both outputs remain in history, only the latest matching revision appears current, and restart retains the relationship.

## M1-08 — Sandbox lifecycle and network boundary

### Goal

Terminal, editor, notebook, and tools share challenge files while untrusted execution remains outside the host control plane.

#### M1-08.a — Container manager

Own `sandbox/docker.py`, `infra/docker/`. Use a versioned Kali-based image, unprivileged user, dropped capabilities, process/memory/CPU limits, no privileged mode, no host credentials, and no Docker socket inside challenge containers. Host-side manager holds narrowly scoped orchestration authority.

Persist sandbox ID, image digest, challenge ID, lifecycle state, and last activity. Create `/work/<challenge-id>` from a named volume. Mount original artifact inputs read-only where tools need them; generated outputs use dedicated writable directories.

##### Lifecycle atomics

Create, start, inspect, stop, and remove are idempotent. Reconcile persisted state with actual containers after restart. Removing a container preserves workspace and evidence unless a separate explicit data-removal operation is requested. Surface unavailable Docker as a capability error; notes and toolbox history remain usable.

#### M1-08.b — Egress enforcement

Start with no external network. Challenge access requires approved exact host/port/protocol rules enforced outside the container. Use a controlled gateway/firewall; an HTTP proxy alone does not constrain arbitrary TCP, UDP, DNS, or raw connections. Prevent direct bridge bypass and block host management endpoints. Resolve names under gateway control and revalidate destinations to avoid rebinding.

##### Acceptance

From terminal, Python, and editor extension host: an approved test destination works; unapproved destinations and Docker/host control endpoints fail. Network restrictions survive container restart. If the implementation cannot enforce this topology on a target platform, keep network disabled and report the capability unavailable.

## M1-09 — Terminal and embedded editor

### M1-09.a — Terminal transport

Own `sandbox/terminal.py`, `api/terminal.py`, `apps/web/src/features/terminal/`. Create PTY sessions only after challenge authorization. WebSocket frames have bounded size; handle resize, stdin, stdout, exit, and heartbeat. Reject unauthorized origins and expired sessions. Apply backpressure rather than unbounded buffering.

#### Transcript and reconnect atomics

Persist timestamped output chunks with sequence numbers and bounded segments. Do not claim raw PTY bytes reliably identify shell commands. Add shell integration or a logged command runner for structured command events; interactive full-screen programs remain transcript-only. Reconnect resumes retained output or explicitly indicates a gap. Do not replay stdin after reconnect.

### M1-09.b — Editor proxy topology

Own `sandbox/editor.py`, `api/editor_proxy.py`, `apps/web/src/features/editor/`. Run code-server on demand in the same challenge workspace. Resolve topology in an implementation spike: publish its port only to host loopback and proxy there, or use an authenticated private service network with no public editor port. Container loopback and host loopback are different namespaces.

#### Integration atomics

- Proxy HTTP and WebSocket upgrades with workbench authentication.
- Test editor assets, base paths, redirects, extension channels, and reconnects.
- Keep editor credentials out of browser-visible URLs and logs.
- Disable telemetry/settings sync and runtime marketplace access.
- Bake approved extensions into the image after license/availability verification.
- Persist settings separately from challenge files.
- Stop idle editor processes without terminating active jobs or deleting files.
- Treat editor-origin requests as untrusted; no elevated control-plane token is exposed to arbitrary extensions.

### M1-09.c — Workspace checkpoints

Own `services/workspaces.py`. Initialize Git once, create debounced checkpoints for tracked text changes, and exclude secrets, artifacts, build outputs, and large binaries. Record checkpoint SHA in events. Restore creates a reviewable diff before applying changes; retain newer history. Checkpoints do not replace immutable artifact storage or full volume backup.

#### Acceptance

Create a Python file in the editor, run it in the terminal, view the output artifact, restart services, and reopen the same file. Direct unauthenticated editor access fails. Restore can recover a prior tracked file without erasing later evidence.

## M1-10 — Layout, navigation, and release gate

### Implementation

Own `apps/web/src/features/workbench/`. Provide dockable file/viewer/board/notebook/toolbox/terminal/editor panes with layout versioning. Persist per-category layouts, validate restored pane IDs, and fall back safely when a pane no longer exists. Command palette uses a typed action registry shared with menu commands. Global shortcuts must not intercept ordinary editor typing.

### Completion evidence

Run one synthetic crypto and one forensic workflow end-to-end, recording expected answers and actual produced evidence. Restart the application midway through one workflow. Verify no model credentials or agent runtime are required. Record measured time and usability observations; do not claim improvement over loose terminals without a baseline comparison.

# M2 — Durable triage and specialized viewers

## M2-01 — Harden background execution

### Goal and dependencies

Depends on M1-04 and M1-08. Extend the initial worker; do not introduce a second competing execution path. Own `jobs/` and integration tests.

#### M2-01.a — Leases and recovery

State machine: `queued → running → succeeded|failed|cancelled`; cancellation may pass through `cancelling`. Workers claim jobs atomically with a lease token and expiry. Heartbeats extend only the matching lease. A stale worker cannot finalize a job after another worker claims it. Persist attempts independently.

#### M2-01.b — Dispatch and retry

Outbox dispatch is at least once; job identity and state guards prevent duplicate active execution. Automatically retry only explicitly idempotent operations. Mark an interrupted non-idempotent operation as uncertain/failed pending review. Use bounded exponential backoff and a maximum attempt count.

#### M2-01.c — Process control and limits

Spawn a process group inside the sandbox. Cancel sends graceful termination then kills the process group after a configured deadline. Enforce wall time, memory, CPU, process, disk, and output quotas. Finalize partial output artifacts with an incomplete marker. A successful child exit is insufficient if declared output validation failed.

##### Acceptance

Kill a worker during execution, recover its lease, and verify one accepted terminal result. Cancel a job that spawns a child and verify both stop. Exhaust output quota without exhausting host memory.

## M2-02 — Triage orchestration and inbox

### Goal

Imported files yield useful, explainable findings without changing board truth automatically.

#### M2-02.a — Planner

Own `services/triage.py`. Subscribe to artifact-import events through the outbox. Check automatic-analysis policy first. Plan hashing, type detection, strings, and entropy; then image, pcap, archive, binary, or memory tasks according to detected capabilities. Do not infer safety from a filename extension. Cache deterministic results by input hash, tool version, and canonical parameters while preserving challenge-scoped access records.

#### M2-02.b — Finding and proposal persistence

Each finding stores title, summary, run/evidence references, detector version, severity/interest label, and deduplication fingerprint. Inbox states are pending, accepted, dismissed, and tried; trying does not automatically accept. Accept creates a hypothesis linked to the proposal. Dismiss records a reason without deleting evidence.

#### M2-02.c — Inbox UI

Own `apps/web/src/features/inbox/`. Show originating artifact, exact operation, result excerpt, and pending job state. Accept/dismiss operations are revision-checked and idempotent. “Try” launches a declared verification/tool operation; arbitrary suggested shell text requires an explicit execution review.

##### Acceptance

Import the same file twice: cached analysis may be reused, duplicate cards are suppressed within the same intended scope, and each import still has an auditable record. Disabled automatic triage creates no execution job.

## M2-03 — Image and steganography viewer

### Goal

Inspect image structure and transformations with reproducible pixel provenance. Own `tools/images/` and `apps/web/src/features/viewers/image/`.

#### M2-03.a — Decode and metadata

Decode in the sandbox with pixel-count and decompressed-size limits. Return width, height, channels, bit depth, orientation, metadata, and preview artifact. Preserve original bytes. Unsupported formats display a download option and capability error.

#### M2-03.b — Transform atomics

Implement channel isolation, bit plane 0–7 for supported 8-bit channels, per-channel histograms, nearest-neighbor zoom, and pixel inspection using source coordinates. EXIF orientation handling is explicit; map displayed coordinates back to the chosen normalized source. Each exported transform is a new artifact linked to its input and parameters.

#### M2-03.c — Stego wrappers

Wrap installed zsteg/steghide/stegseek capabilities as typed jobs with limits and explicit parameter schemas. Missing executables are unavailable capabilities, not empty findings. Do not automatically launch expensive cracking on upload.

##### Acceptance

A synthetic image with known channel bits produces exact expected bit planes and pixel values; oversized dimensions are rejected before allocation.

## M2-04 — Packet capture viewer

### Goal

Inspect conversations and streams without transferring whole captures to the browser. Own `tools/network/` and `apps/web/src/features/viewers/pcap/`.

#### M2-04.a — Index and filter

Use a version-pinned tshark wrapper with argument arrays. Cache parsed indexes by artifact hash and parser version. Return paginated packet summaries and conversations. Treat display filters as parser inputs, not shell fragments; return useful parser errors without exposing host paths.

#### M2-04.b — Stream and export

Stable packet references include capture hash and frame number. Stream references include protocol and stream ID. Preserve direction and timestamps; expose binary stream bytes as artifacts. Exported objects record contributing packets and extraction tool version. TLS keylogs are sensitive artifacts with restricted access and exclusion from model context by default.

##### Acceptance

A synthetic capture yields expected conversations, payload bytes, frame references, and exported object hashes. Malformed captures produce bounded failures; invalid filters leave the previous valid result visible with an error.

## M2-05 — Audio viewer

### Goal

Provide waveform, spectrogram, and bounded audio decoding. Own `tools/audio/` and `apps/web/src/features/viewers/audio/`.

#### Implementation atomics

Decode audio in sandboxed jobs with duration/sample limits. Return multiresolution waveform peaks rather than every sample. Spectrogram records window function, FFT size, hop length, scale, and channel mix. Time selections use integer sample ranges plus sample rate. DTMF/Morse results are hypotheses with timing evidence; ambiguous symbols remain marked uncertain.

##### Acceptance

Known tones appear at expected frequency/time bins within declared resolution. Exporting a selection produces the exact requested sample interval, and a corrupt file fails without crashing the panel.

## M2-06 — Memory and archive inspection

### M2-06.a — Memory summaries

Own `tools/memory/` and `apps/web/src/features/viewers/memory/`. Detect supported Volatility 3 capabilities and required symbol availability. Implement process list, command line, network connection, and file-scan jobs first. Normalize rows while retaining raw output artifacts and plugin/version metadata. Missing symbols produce an actionable unavailable-analysis state, never a claim that no processes exist.

#### Extraction atomics

Process/file dumps are explicit jobs; outputs become derived artifacts with address/process/plugin provenance. Restrict output paths to job staging directories. Pagination is over stored normalized results, not repeated full-dump analysis.

### M2-06.b — Archive/document inspection

Own `tools/files/`. List before extracting. Enforce cumulative uncompressed bytes, entry count, nesting depth, time, and expansion limits. Reject absolute paths, traversal, device nodes, and escaping symlinks. Never mount an image on the host. Initial image inspection uses userspace tools inside the sandbox; privileged mounting is unavailable.

##### Acceptance

Known memory fixtures produce expected rows when licensed fixtures and symbols are available; otherwise CI validates wrappers with captured fixtures and clearly labels missing live coverage. Archive traversal and expansion-bomb fixtures fail without creating files outside staging.

## M2-07 — Integration and release gate

### End-to-end scenario

Import image, pcap, audio, and supported memory fixtures; observe queued/running/completed triage, inspect each viewer, accept one finding as a hypothesis, attach evidence, and rerun its operation. Restart during triage and verify recovery. Confirm all generated artifacts lead back to their originals.

### Definition of done

Deliver capability diagnostics, fixture manifests with hashes/licenses, recorded verification results, migration notes, and user-visible errors for missing optional tools. No viewer may substitute demo data for a failed or absent backend. Unimplemented capability cards remain explicitly unavailable.



---

# M3 — Evidence-linked sidekick

## M3 execution contract

Goal: a human selects challenge material, asks a question, sees a streamed answer with inspectable evidence, and optionally accepts a proposal. The existing manual workbench remains usable when the agent runtime is absent.

Dependencies: M0 domain/auth/event contracts, M1 artifact/board/tool/sandbox services, and M2 durable jobs. Read the root execution specification before starting. IDs in this document are independently assignable tasks; complete dependencies before integration.

Ownership: an agent-runtime subagent owns `src/ctf_workbench/agents/`; an MCP subagent owns `src/ctf_workbench/mcp/`; a frontend subagent owns `apps/web/src/features/sidekick/`; an editor subagent owns `packages/editor_extension/`. The coordinator owns migrations, API registration, dependency manifests, generated clients, and shared schemas. Request coordinator changes instead of concurrently editing shared files.

## M3-01 — Runtime compatibility boundary

### Goal and deliverables

Create `agents/runtime.py`, `agents/opencode_adapter.py`, and adapter contract tests. All application code depends on a runtime protocol rather than opencode endpoint names.

#### M3-01a — Verify the installed runtime

Record the installed opencode version and consult its matching official documentation during implementation. Verify create-session, prompt, abort, event-stream, permission, working-directory, MCP configuration, and usage-reporting capabilities against a local test instance. Record exact versions and unsupported features in an architecture decision. Do not infer endpoint names or agent-definition directories from this planning document.

##### Expected result and acceptance

A smoke test creates an isolated session, receives streamed content, aborts it, and confirms termination. If the runtime cannot isolate writes or enforce tools, mark delegated execution unavailable; do not silently fall back to an unrestricted runtime.

#### M3-01b — Define the runtime protocol

Provide `create_session(scope, workspace, model, permissions)`, `send_prompt(runtime_id, prompt, request_id)`, `subscribe(runtime_id, cursor)`, `abort(runtime_id)`, and `get_status(runtime_id)`. Normalize results into application-owned DTOs. Represent unavailable usage fields as null, not zero.

##### Failure behavior

Map transport errors to `runtime_unavailable`, invalid configuration to `runtime_misconfigured`, and runtime rejection to `runtime_rejected`. Retry read-only status calls with bounded backoff. Never automatically resend a prompt after an ambiguous timeout unless the runtime supports verified idempotency.

### Integration and verification

Use deterministic fake-runtime fixtures for tests; live-provider tests are opt-in. Assert the manual challenge page loads when the runtime is stopped. No other module imports opencode-specific SDK types.

## M3-02 — Session persistence and API

### Goal and deliverables

Create `agents/service.py`, `agents/schemas.py`, and API handlers through the coordinator. Sessions survive browser reconnects and never inherit a different challenge's permissions.

#### M3-02a — Persist the session contract

Fields: `id`, `challenge_id`, `created_by`, `runtime_id`, `mode`, `state`, `model_ref`, `context_artifact_id`, `policy_version`, `created_at`, `started_at`, `ended_at`, `last_runtime_cursor`, `error_code`. Modes are `ask`, `review`, `brainstorm`, `delegate`; only ask/review are exposed in M3.

##### State transitions

Use `created -> starting -> running -> completed|failed|cancelled`; `starting` may also fail/cancel. Cancellation first records a request and then aborts runtime and child jobs. Record `termination_unconfirmed` if the runtime cannot confirm shutdown; never label continued execution cancelled successfully.

#### M3-02b — Expose session commands

`POST /api/v1/challenges/{id}/sessions` accepts `mode`, `message`, `selection`, `model_ref`, and `request_id`; returns 202 with the application session ID. `GET /api/v1/sessions/{id}` returns status and persisted messages. `POST /api/v1/sessions/{id}/cancel` is idempotent. Additional messages use `POST /api/v1/sessions/{id}/messages` with a unique client request ID.

##### Validation and concurrency

Resolve identity and challenge authorization server-side. Reject disabled assistance before contacting the runtime. Serialize prompts within one session; return a conflict if a new prompt is submitted while a turn is running unless an explicitly implemented queue handles it. Use a unique constraint for `(session_id, request_id)`.

### Acceptance

Duplicate create/message requests produce one runtime action. Restart recovery reconciles persisted running sessions with runtime state. Missing runtime sessions become failed with a recoverable UI explanation, never silently disappear.

## M3-03 — Context builder and data boundaries

### Goal and deliverables

Create `agents/context.py` with a deterministic, inspectable `ContextPackage` serialized to an artifact before dispatch.

#### M3-03a — Assemble scoped context

Include challenge title/description, authorized scope, assistance policy, user request, selected reference, relevant confirmed facts, active hypotheses, and relevant dead ends. Each included item contains its ID, status, revision, and evidence IDs. Artifact content is passed as bounded slices; large files remain references.

##### Budget algorithm

Reserve room for the user request and policy first, selection second, confirmed facts third, relevant dead ends fourth, active leads fifth. Truncate by explicit section budgets and emit an omission summary. Reject an individually oversized request instead of cutting policy instructions. Record tokenizer identity or estimation method.

#### M3-03b — Prevent scope and secret leakage

Resolve every referenced ID using the session's challenge authorization. Shared competition artifacts require explicit access checks. Exclude platform credentials, provider keys, private configuration, and secret values unless an authorized tool operation specifically requires them. Challenge content is untrusted data, never policy text.

##### External model behavior

When external models are forbidden, reject external model dispatch. Otherwise show which text/image slices will be sent and persist a context manifest. Local editing must work without any external model. Selection sharing from the editor is opt-in and can be disabled immediately.

### Acceptance

Identical state and request produce identical context ordering. Tests prove a foreign challenge ID and embedded instructions inside an artifact cannot expand scope. A dead-end fixture appears in the resulting context with its reason and evidence.

## M3-04 — Shared MCP execution surface

### Goal and deliverables

Create `mcp/server.py`, `mcp/tools.py`, and schema/authorization tests. Wrappers call the same domain services as HTTP handlers; do not duplicate algorithms or database writes.

#### M3-04a — Register initial tools

Expose `artifact_get`, `board_list`, `board_propose_lead`, `board_attach_evidence`, `tool_run`, `notebook_append`, and `flag_candidate_propose`. `artifact_get` accepts an artifact ID and bounded byte range, never an arbitrary host path. `tool_run` accepts registry tool ID, typed parameters, and input artifact references, returning a job/run ID and status.

##### Proposal mutation rules

`board_propose_lead` creates an inbox proposal authored by the session, with proposed text and evidence IDs. It cannot set `confirmed`. `board_attach_evidence` attaches only validated evidence to session-owned proposals; modifying accepted board records requires the normal authorized service. `notebook_append` writes an attributed proposal block into the agent-output section, without replacing human notes.

#### M3-04b — Bind credentials to a session

Issue short-lived capability credentials containing session and challenge identity plus allowed tool IDs. Validate expiry, revocation, and current policy on every call. Do not trust challenge IDs supplied in tool arguments. Revoke on cancellation and completion.

##### Execution restrictions

Reject arbitrary shell strings through registered analysis tools. Tools requiring network or unknown binary execution request approval according to current autonomy. Any runtime-native shell or file tools must receive equivalent technical restrictions; disabling only MCP tools is insufficient.

### Acceptance

The same fixture called through HTTP and MCP yields equivalent structured output and provenance. A forged challenge argument, expired credential, and request to confirm a fact are denied and audited.

## M3-05 — Event bridge and sidekick UI

### Goal and deliverables

Create `agents/events.py` and the sidekick feature with composer, message list, tool cards, evidence drawer, cancellation, and reconnect status.

#### M3-05a — Normalize runtime events

Map runtime deltas into `session.started`, `message.delta`, `tool.started`, `tool.completed`, `usage.updated`, and terminal session events. Persist normalized messages and evidence links. Assign application sequence numbers and deduplicate source event IDs. If source IDs are absent, document the weaker replay guarantee and reconcile from authoritative runtime messages.

##### Stream recovery

Browser subscriptions resume from the last application sequence. If history is unavailable, return a resync instruction and fetch persisted session state. Do not append the same assistant text twice after reconnect. Keep raw runtime payloads in a restricted diagnostic store if retained; redact secrets.

#### M3-05b — Validate citations

Use structured citation objects containing artifact/run/item ID and optional range. Resolve them server-side and verify access and bounds. Invalid references remain visible as unsupported claims, not clickable evidence. Do not mark prose verified merely because it contains a valid citation.

#### M3-05c — Render human actions

Show selected context before sending; show author, session state, evidence, and tool duration on responses. Offer “Accept as lead,” “Dismiss,” and “Open evidence.” Acceptance creates a hypothesis unless the human explicitly invokes the separate confirmation action. Preserve pending input when a request fails.

### Acceptance

End-to-end: select known ciphertext, send a question to the fake runtime, observe one tool run, inspect its output, accept the proposed lead, refresh, and see the same provenance. Keyboard users can reach all actions and focus returns to the triggering control after closing a drawer.

## M3-06 — Companion editor extension

### Goal and dependencies

Depends on M3-02 through M3-05 and the M1 embedded editor. Own `packages/editor_extension/`; request coordinator changes for image packaging and credentials.

#### M3-06a — Reuse integration only when suitable

Inspect the installed opencode editor integration during implementation. Reuse its transport only if it supports the workbench's scoped identity, evidence references, and policy controls. Record the decision; implement a thin companion extension regardless for workbench-specific commands.

#### M3-06b — Implement sidebar and commands

Provide Board, Artifacts, and Inbox views. Commands: add selection as lead, ask sidekick, attach file/line evidence, run a registered toolbox operation, and propose a flag. Resolve selections to workspace-relative path, current content hash, line range, and checkpoint ID. Snapshot unsaved selected text as a derived artifact before using it as evidence.

##### Authentication and lifecycle

Bootstrap a short-lived per-editor capability through the authenticated editor session. Do not store control-plane admin credentials in extension settings. Reconnect with backoff; revoke on logout. Turning off selection sharing stops publications and clears ephemeral active-selection state.

#### M3-06c — Templates and logged execution

Add solver templates for Python, pwntools, RSA, and z3 as explicitly selected snippets. Run commands through the shared job service so outputs are persisted. Do not execute a template on insertion. CodeLens links open stable workbench evidence references.

### Milestone exit gate

The browser and embedded editor can both ask about a selection, inspect identical evidence, and accept a lead. Agent-off mode generates no model traffic. The runtime cannot mutate confirmed board state or the main workspace through an alternate tool path.

# M4 — Suggestions with reproducible verification

## M4-01 — Proposal lifecycle

### Goal and deliverables

Extend the existing inbox service rather than creating a second suggestions database. Proposal fields include source session/run, evidence IDs, text, fingerprint, revision, state, dismissal reason, and linked board item.

#### M4-01a — Implement state transitions

States: `pending`, `accepted`, `dismissed`; verification attempts are separate records so trying a suggestion does not implicitly accept it. Accept/dismiss use expected revision and idempotency key. Double acceptance returns the original board item. Dismissal can optionally create a dead-end item with the human's reason.

#### M4-01b — Implement UI actions

Show accept, dismiss, and try. A pending try displays progress and links its run. Distinguish “check passed” from “human confirmed.” Reject stale writes with current state so the client can reconcile without duplicating records.

### Acceptance

Concurrent accept requests create one board item. A failed check leaves the proposal pending with a failed attempt; it does not erase its previous evidence.

## M4-02 — Structured verification

### Goal and deliverables

Create `agents/verification.py` and typed specifications. A specification contains tool ID/version, exact input hashes, parameters, expected predicate, and claim revision.

#### M4-02a — Allow bounded predicates

Initially support exact output hash, exact decoded bytes, regex match using a bounded engine, and structured-field equality. Store the expected value and encoding explicitly. Arbitrary verifier code is a separate sandbox job requiring normal execution policy, never Python `eval` in the API process.

##### Promotion semantics

Promotion to `verified` requires a successful run and predicate for the same claim revision. A later claim edit invalidates the prior verification association. A regex match verifies the match, not remote flag acceptance. Only a human confirmation command produces `confirmed`.

#### M4-02b — Preserve replay identity

Record image digest, tool version, input hashes, and environment requirements. If the required version is unavailable, report `not_reproducible_here` rather than rerunning silently with a different implementation. A deliberate updated-version check is a new verification attempt.

### Acceptance

Test successful hash equality, failed equality, stale claim revision, unavailable version, and malicious predicate input. Each attempt has a distinct run and evidence chain.

## M4-03 — Bounded watchers

### Goal and deliverables

Create `agents/watchers.py` with event subscriptions for new artifacts, verified keys, and selected board changes. Watchers generate proposals only.

#### M4-03a — Schedule deterministically

Fingerprint `(watcher_version, challenge_id, input_hashes, relevant_state_revision)`. Enforce one active run per fingerprint, a configurable cooldown, and per-challenge daily budget. Ignore watcher-generated events unless a documented downstream rule explicitly consumes them; prevent self-triggering loops.

#### M4-03b — Apply policy and cancellation

Level 0 disables model watchers. Level 1 permits suggestions only from explicitly enabled bounded watcher policies; automatic executable analysis requires level 2 or explicit human initiation. Recheck policy when dequeuing and before dispatch. Policy downgrade cancels incompatible queued work.

### Milestone exit gate

A repeated upload cannot trigger an unbounded suggestion loop. A suggestion's “Try” action creates reproducible evidence and promotes only the tested claim. Dismissed theories are included in later relevant context.

# M5 — Scoped delegated tasks and advanced analysis

## M5-01 — Delegation contract and budgets

### Goal and deliverables

Extend sessions with task objective, allowed tools, artifact scope, worktree reference, wall-clock deadline, token limit, cost limit, and report artifact. Require explicit task submission; do not turn ordinary chat into autonomous delegation.

#### M5-01a — Enforce budgets

Reserve estimated budget before starting a model call; reconcile actual usage afterward. Deny new calls when the reserve is exhausted. Stop runtime and child jobs at wall-clock expiry. Missing provider usage is `unknown`; display estimated spend separately from reported spend. Document that in-flight provider calls may exceed an approximate token/cost cap.

#### M5-01b — Apply autonomy consistently

Level 1 can read approved artifacts and write only scratch output. Level 2 can run registered safe analysis automatically. Level 3 can execute delegated work within its sandbox and scope. Network, VM, and flag-submission policies remain independently enforced; level 3 does not grant platform credentials or host filesystem access.

### Acceptance

Use a fake clock and runtime to verify budget exhaustion, cancellation propagation, no further tool calls after revocation, and a partial report after timeout.

## M5-02 — Worktrees and patch acceptance

### Goal and deliverables

Create `agents/workspaces.py` and patch-review UI. The human workspace remains authoritative; agent edits are reviewable outputs.

#### M5-02a — Create isolated session workspaces

Checkpoint eligible source files, record base commit, and create a worktree named from the application session ID. Exclude credentials, large artifacts, and generated caches from Git; expose required artifact bytes read-only. At low autonomy use scratch storage with the human workspace read-only.

##### Concurrency behavior

Publish advisory file ownership markers. When a human saves a changed file, notify the session and mark its base stale. Never assume the marker is a lock. Rebase/restart work only after preserving the session's current diff; do not overwrite either side.

#### M5-02b — Generate and apply patches

Store patch artifact, base commit, affected paths, file hashes, and summary. Validate all paths remain inside the workspace and reject escaping symlinks. Apply only selected hunks whose base still matches; otherwise open conflict review. Recheck hashes immediately before application under a workspace mutation lock.

##### Acceptance and rollback

Create a pre-apply checkpoint, apply atomically where possible, emit an event, and create a post-apply checkpoint. On partial failure restore only the files affected by this transaction. Never reset unrelated human changes. Binary replacements require explicit whole-file acceptance.

### Acceptance

Tests cover clean apply, overlapping edits, unrelated human changes, path traversal, symlink escape, binary change, and interrupted application. Rejecting a patch leaves the human workspace unchanged.

## M5-03 — Ghidra integration

### Goal and deliverables

Own `src/ctf_workbench/tools/ghidra/` only by coordinator assignment. Add headless analysis, function list, decompilation, xrefs, strings, rename, and retype operations using the shared run service.

#### M5-03a — Cache and isolate projects

Key analysis projects by input SHA-256, Ghidra version, processor selection, and analysis options. Use an exclusive project lock for mutations. Publish incremental progress; cancellation must release locks and leave incomplete projects marked unusable until repaired or rebuilt.

#### M5-03b — Persist annotations and stable references

Identify functions using artifact hash, image base, and address, not display name. Rename/retype requests carry expected project revision. Preserve prior values in events. Export annotation snapshots as artifacts so evidence survives project regeneration.

#### M5-03c — Present analysis

Render function list, read-only decompiler/disassembly, xrefs, and strings. The editor extension exposes decompiler virtual documents. Send rename requests through the service; refresh affected documents only after the transaction succeeds.

### Acceptance

A known fixture produces expected functions; rename survives restart; conflicting revisions are rejected; cancelling analysis does not expose partial results as complete.

## M5-04 — Memory workflows and reports

### Goal and deliverables

Extend M2's memory browser with versioned Volatility workflows: process list, command lines, network connections, file scan, dump file/process, registry, and suspicious-region inspection.

#### M5-04a — Handle symbols and dependencies

Record plugin version, symbol identifiers, input hash, and command arguments. Use an approved local symbol cache. Missing symbols produce a structured prerequisite error; any download is a separate network-policy-controlled job. Preserve stderr and partial output without marking the job successful.

#### M5-04b — Promote outputs into artifacts

Every dump receives its own hash, parent artifact relationship, originating run, and object identifier. Never use an untrusted plugin-supplied filename directly as an output path. UI pagination works over persisted structured rows rather than repeatedly invoking the plugin.

#### M5-04c — Produce a task report

On success, failure, cancellation, and timeout, create a report with objective, completed actions, findings, evidence links, generated artifacts, proposed patches, spend, elapsed time, and unresolved questions. Unsupported claims are explicitly labeled. Reports cannot automatically confirm board items.

### Milestone exit gate

A delegated fixture task runs within scope, produces artifacts and a reviewable patch, survives browser reconnect, and terminates on cancellation. Ghidra and memory outputs retain stable references. A stale patch cannot overwrite newer human edits. All subagents provide changed paths, acceptance evidence, unresolved constraints, and requested shared-file edits to the coordinator.


---

# M6 — Hunts, cross-challenge reasoning, and platform integration

## Execution boundary and ownership

This file specifies implementation tasks, not already implemented functionality. Execute after the shared challenge, artifact, event, policy, job, and proposal services exist. Each numbered task is independently assignable after its prerequisites pass. Do not replace those services with feature-specific persistence or agent execution paths.

Own feature files under `src/ctf_workbench/hunts/`, `platforms/`, `collaboration/`, `vms/`, `writeups/`, `evaluation/`, and matching `apps/web/src/features/` directories. Request migration and shared-contract changes through the integrating agent. Each task includes its own tests in the corresponding test directory. Agents proposing board changes must use the existing proposal service.

### Common feature completion rule

#### Deliverable contract

For each task deliver typed input/output models, service implementation, authenticated API integration, accessible UI states, meaningful acceptance tests, and documentation of environment requirements. Existing tool operations must also be available through the common MCP registry without duplicating algorithms. Do not mark an unavailable external integration complete using a mock-only test.

##### Cross-feature invariants

All IDs are opaque identifiers. Scope every query by authorized competition and challenge. Every mutation writes its audit event transactionally. Reject stale revisions with HTTP 409. User text and downloaded HTML are untrusted; render text safely and never execute imported scripts in the workbench origin. Cross-challenge access must remain within an explicitly authorized competition.

## M6-01 — Thought board and typed relationships

### Goal and user-visible behavior

Users can connect puzzles, artifacts, claims, and answers without duplicating the underlying objects. The graph is another view of existing data; deleting a visual node from a saved view does not delete its source object.

#### Dependencies and owned files

Depends on foundation links, board services, and artifact references. Own `hunts/graph.py`, `hunts/schemas.py`, and `features/thought-board/`. Add React Flow through the frontend dependency owner.

##### M6-01a — Typed edge validation

Implement `create_link(actor, competition_id, source_ref, target_ref, relation, expected_revision)` using the common links repository. Allow `derived_from`, `unlocks`, `contradicts`, `same_key_as`, and `feeds_meta`. Require artifact endpoints for `derived_from`; require a meta puzzle as the target of `feeds_meta`. Reject missing endpoints, cross-competition endpoints, self-links, and duplicate identical directed edges. Treat `same_key_as` as undirected by canonicalizing endpoint order.

##### M6-01b — Graph projection and layout persistence

Implement `GET /api/v1/competitions/{id}/graph?challenge_id=&cursor=&limit=` with node and edge pages and total counts. Return node labels, source references, status, and category; omit secret values. Store user layout positions separately from semantic edges, keyed by user and view ID. Use the foundation pagination limits: default 50, maximum 200 nodes per page. Load neighbors on demand rather than recursively fetching the whole graph.

##### M6-01c — Interactions and accessibility

Provide node search, category/status filters, keyboard-accessible relation creation, and an equivalent table view. Clicking a node opens its existing detail pane. Edge deletion requires the current revision and emits a link event. Preserve pan and zoom per saved view. Empty graphs explain how to add the first link.

##### Acceptance and deliverables

Test cross-competition rejection, symmetric-edge deduplication, stale updates, and saved-layout isolation. Browser test: create two puzzle nodes, link an answer to a meta, refresh, and verify that both the relationship and positions remain.

## M6-02 — Meta slots and theme tracker

### Goal and user-visible behavior

A meta puzzle displays required answer slots and source puzzles. Themes are evidence-linked hypotheses rather than silently inferred facts.

#### Dependencies and owned files

Depends on M6-01 and the proposal service. Own `hunts/metas.py`, `hunts/themes.py`, and their frontend panels.

##### M6-02a — Ordered meta slots

Create `meta_slots(id, meta_challenge_id, ordinal, label, source_challenge_id, answer_item_id, revision)`. Enforce unique ordinal per meta. Slot values reference board items instead of copying answer strings. Return `filled_count`, `total_count`, and slot claim status. Hypothesis answers count as proposed, not confirmed filled slots. Reordering submits the complete ordered slot-ID list and validates exact membership.

##### M6-02b — Theme records

Store a display label, normalized search label, evidence references, and proposal/board reference. Exact normalization uses Unicode NFC and case folding; retain original spelling. Automatic recurrence detection may propose matching labels but cannot merge distinct themes without human action. A theme detail lists where it was observed and where a related key succeeded or failed.

##### M6-02c — Known-key references

Expose known-key metadata across authorized challenges. Actual passwords and key material require a separate reveal/use operation with an event, never graph labels or general log payloads. Cross-challenge decryption suggestions reference key IDs and destination artifacts; execution uses the scoped tool service.

##### Acceptance and deliverables

Test slot ordering conflicts, source item deletion/tombstones, confirmed versus proposed tallies, Unicode matching, and absence of raw secrets in graph responses. A human must be able to trace every theme occurrence to evidence.

## M6-03 — Puzzle ingest and wordplay tools

### Goal and user-visible behavior

Import text, images, and authorized web captures; search local wordlists and perform reproducible letter transformations.

#### Dependencies and owned files

Depends on artifact ingestion, sandbox jobs, and network policy. Own `hunts/ingest.py`, `tools/wordplay/`, and `features/hunts/`.

##### M6-03a — Text and image ingest

Save pasted text as immutable UTF-8 artifacts retaining newline content. Save a separate normalized search representation if necessary. Image imports reuse upload and image-triage services. OCR output is a derived artifact with image-region coordinates, engine version, and confidence; OCR text is not a confirmed answer.

##### M6-03b — Web capture

Run Playwright in an isolated job after scope approval. Produce screenshot, saved HTML, final URL, redirect chain, capture timestamp, and resource-failure summary. Check every redirect and network request against scope, including resolved IP addresses. Deny access to loopback, host services, and metadata endpoints unless explicitly configured for an authorized challenge. Display captured HTML as escaped text or a sanitized document on an isolated origin.

##### M6-03c — Wordlist indexing

Store wordlist content hash, language, license/source metadata, normalization settings, and indexed version. Preserve original entries alongside normalized search keys. Build indices for sorted-letter signatures, lengths, and normalized tokens. Do not download dictionaries implicitly; ship a redistributable fixture and support explicit imports.

##### M6-03d — Word operations

Implement anagram search by normalized character counts; wildcard letters consume unmatched counts. Implement crossword pattern matching with explicit `?` for one character and fixed total length. Implement acrostic/telestich and every-Nth-letter operations with explicit units (`characters`, `words`, `lines`), start index, and one-based displayed positions. Return selected source positions with output.

##### M6-03e — Pattern search and homophones

Implement bounded regex searches in a cancellable worker with timeout and result limit. Do not advertise compatibility with an external pattern language until a grammar and fixtures exist. Homophone lookup uses an imported pronunciation dictionary and reports dialect/source; absent entries produce no result, not a generated assertion.

##### Acceptance and deliverables

Test accents, punctuation, blank lines, duplicate words, wildcard counts, invalid patterns, expensive regex cancellation, and off-by-one extraction. Network tests must prove redirect policy enforcement. UI and MCP must produce the same word-operation result IDs.

## M6-04 — Platform adapter contract

### Goal and user-visible behavior

Synchronize supported CTF platforms while retaining locally authored notes and evidence.

#### Dependencies and owned files

Depends on challenge APIs, credential storage, jobs, and approval service. Own `platforms/base.py`, `platforms/ctfd.py`, `platforms/rctf.py`, and `features/platforms/`.

##### M6-04a — Capability-based interface

Define `PlatformAdapter` operations `list_challenges(cursor)`, `get_challenge(external_id)`, `download_attachment(ref)`, `get_solve_state()`, `submit_answer(external_id, answer, request_id)`, and optional `start_instance(external_id)`. Return explicit unsupported capability errors. Pin adapter contract fixtures to the verified server/API version; inspect current official documentation during implementation.

##### M6-04b — Synchronization semantics

Use unique `(competition_id, platform, external_id)` mapping. Update remote title, points, description, hints, and remote solve state while preserving local board, owner, notes, and status overrides. Save source snapshots and changed-field events. Paginate incrementally and persist checkpoints only after a page commits. Mark disappeared challenges unavailable rather than deleting them.

##### M6-04c — Download semantics

Stream downloads to the artifact importer with size limits and hash verification when supplied. Re-check scope on redirected attachment URLs. Retry safe reads with bounded backoff, respect rate limits, and display partial sync errors. Never log authorization headers or tokens.

##### M6-04d — Generic JSON importer

Publish a versioned JSON schema containing competition metadata, challenges, descriptions, categories, points, and attachment references. Validate the entire manifest before writes. Provide a dry-run summary of creates, updates, and conflicts. Reject local path references outside the selected import root.

##### Acceptance and deliverables

Contract tests cover pagination, duplicate sync, partial downloads, expired credentials, missing capabilities, and edited local notes. Integrate a local fixture server; record a separate live smoke-test result when credentials and an authorized platform are available.

## M6-05 — Flag and answer queue

### Goal and user-visible behavior

Candidate creation never submits an answer. Submission requires a human approval tied to the exact candidate and destination.

#### Dependencies and owned files

Depends on M6-04 and shared approvals. Own `platforms/submissions.py` and `features/submissions/`.

##### M6-05a — Candidate creation

Store candidate bytes/text, challenge ID, evidence references, creator, normalized fingerprint, format-check result, and state. Do not silently trim or alter flag text; show any suggested normalization separately. Validate configured patterns in a bounded engine. A failed format check may be explicitly overridden by an authorized human with a reason.

##### M6-05b — Submission state machine

Implement `proposed -> approved -> queued -> submitting -> accepted|rejected|unknown|failed`. Dismissal is allowed before submitting. Approval records candidate hash, platform destination, approving principal, and expiry. Any candidate/destination edit invalidates approval. Use a unique dispatch key and transactionally claim queued records.

##### M6-05c — Ambiguous result handling

On timeout after sending, mark `unknown` and reconcile through platform solve state where supported. Do not automatically resubmit unknown attempts. Distinguish transport failure before send from an uncertain response after send. Apply competition and challenge cooldowns; honor server retry hints. Redact answers from routine logs while retaining access-controlled attempt records.

##### Acceptance and deliverables

Prove agents cannot approve, stale approvals cannot submit, two workers cannot submit the same queued attempt, and response loss produces `unknown`. Browser test covers propose, inspect evidence, approve, queue, and display accepted/rejected response.

# M7 — Virtual machines and collaboration

## M7-01 — VirtualBox lifecycle and snapshots

### Goal and user-visible behavior

Manage explicitly registered local VMs with traceable snapshots and controlled operations.

#### Dependencies and owned files

Depends on jobs, approvals, and policy. Own `vms/virtualbox.py`, `vms/service.py`, and `features/vms/`. The VM adapter runs in a trusted host helper; do not place arbitrary host execution behind the sandbox tool interface.

##### M7-01a — Typed host adapter

Implement list, inspect, start, graceful stop, snapshot, restore, screenshot, guest execution, and guest file transfer. Invoke a configured VBoxManage executable using argument arrays, never interpolated shell strings. Parse machine-readable output and retain sanitized raw diagnostics as evidence. Address VMs by registered UUID, not user-supplied command fragments.

##### M7-01b — Mutating operation protocol

Require an approval bound to VM UUID, operation, parameters, and expiry. Serialize mutations per VM. Before agent guest execution or file writes, create a snapshot and verify its identifier before continuing. Snapshot failure aborts the requested mutation. Restore shows the selected snapshot and destructive effect, then requires fresh approval. Read-only inspection does not require a snapshot.

##### M7-01c — Guest operations and UI

Store guest credentials outside prompts and event payloads. Enforce registered guest paths for transfers and file-size limits. Show state transitions, last successful snapshot, operation progress, and errors. Screenshots become access-controlled artifacts. Unsupported guest additions produce actionable capability errors.

##### Acceptance and deliverables

Test malicious arguments, stale approvals, concurrent operations, snapshot failure, process timeout, and missing VirtualBox. Run a disposable VM smoke test; if unavailable, mark the live acceptance gate blocked instead of claiming verification.

## M7-02 — Team identities, roles, and database migration

### Goal and user-visible behavior

Multiple authenticated users share competitions without gaining unintended execution or approval rights.

#### Dependencies and owned files

Depends on established actor identities and permission checks. Own `collaboration/permissions.py` and identity integration. The integration owner controls shared auth middleware and migrations.

##### M7-02a — Role matrix

Implement competition membership with viewer, operator, and admin roles. Viewers read permitted records; operators edit notes/board, run scoped tools, and create proposals; admins additionally approve submissions, change policy, control VMs, and manage membership. Agent identities are never admins. Enforce permissions in services, not only route handlers or UI controls.

##### M7-02b — PostgreSQL migration path

Make repository SQL portable, add PostgreSQL integration tests, and implement a maintenance-mode export/import preserving IDs, timestamps, revisions, relationships, and artifact hashes. Validate row counts and referential integrity before switching configuration. Keep the original SQLite database as a backup. Do not attempt live bidirectional replication.

##### M7-02c — Shared execution isolation

Use separate editor user-data directories per human. Keep workspace ownership visible. Require branches/worktrees for concurrent code edits; do not imply that Yjs notebook collaboration provides source-file merge safety. Reserve budget before session start and release unused reservation at terminal state, including crash reconciliation.

##### Acceptance and deliverables

Test the complete role matrix at service level, revoked membership during WebSocket sessions, migration with linked evidence, and simultaneous budget reservation. Remote team mode must not start without configured authentication and transport security.

## M7-03 — Collaborative notes, presence, and claims

### Goal and user-visible behavior

Notebook text merges live while board transitions remain authoritative server operations.

#### Dependencies and owned files

Depends on M7-02 and existing notebook revisions. Own `collaboration/documents.py`, `collaboration/presence.py`, and frontend providers.

##### M7-03a — Yjs document persistence

Store document updates with ordered sequence numbers and compacted snapshots. Authorize the document before WebSocket upgrade and each reconnect. Enforce update/message size limits. Associate updates with actor and document ID; snapshot notebook versions used in evidence. Persist before acknowledging durable updates.

##### M7-03b — Notebook conversion

Migrate each existing note to one Yjs document exactly once, recording source revision and migration event. Preserve runnable cell IDs and immutable execution outputs; concurrent text editing does not rewrite an old cell run. Mark output stale when current code differs from executed code.

##### M7-03c — Presence and ownership

Presence is ephemeral with a 30-second heartbeat and 90-second expiry. Challenge claims and inbox work claims are durable leases with owner, expiry, and revision. Acquisition uses compare-and-swap; a second claimant gets 409 with current owner metadata. Expired claims can be acquired and emit an event.

##### Acceptance and deliverables

Test disconnected simultaneous edits, reconnect after compaction, revoked access, oversized updates, claim races, and stale notebook outputs. Browser test uses two sessions to edit a shared note and contend for one inbox card.

## M7-04 — Notifications

### Goal and user-visible behavior

Users explicitly configure notifications for solves, waiting approvals, and completed reports.

#### Dependencies and implementation

Depends on transactional events and credential storage. Own `collaboration/notifications.py`. Store destination secrets server-side. Use an outbox consumer with deduplication key `(event_id, destination_id, template_version)`. Send concise messages containing application references and no flag values, raw keys, or model context. Provide an opt-in test-delivery action and visible delivery status.

##### Failure handling and acceptance

Retry retryable failures with a capped backoff; disable or surface persistent authorization failures. Do not claim exactly-once delivery where the remote webhook lacks idempotency. Test duplicate events, endpoint errors, secret redaction, disabled destinations, and rate limiting.

# M8 — Writeups, retrieval, and evaluation

## M8-01 — Timeline and evidence-linked export

### Goal and user-visible behavior

Turn recorded work into an editable writeup without converting unsupported agent claims into facts.

#### Dependencies and owned files

Depends on event history, immutable evidence, and notebook snapshots. Own `writeups/timeline.py`, `writeups/export.py`, and `features/writeups/`.

##### M8-01a — Timeline projection

Page events by stable sequence, group tool runs with their outputs, and retain original actor and claim status. Filter by artifact, actor, event type, and time range. Missing referenced artifacts render an explicit unavailable entry; do not omit them silently.

##### M8-01b — Deterministic writeup draft

Generate Markdown sections for challenge, observations, attempts, confirmed solution, and reproducibility. Include artifact hashes, tool/image versions, commands, and evidence links. Label hypotheses and failed attempts. Default to redacting platform tokens, passwords, and flags; allow explicit export selection for challenge answers without revealing application credentials.

##### M8-01c — Optional model-assisted prose

Pass only selected evidence and current policy-approved context to the existing agent service. Require returned references to known evidence IDs. Save generation inputs and draft revision; never overwrite user edits. Render unsupported text as unverified until edited or linked to evidence.

##### M8-01d — Portable bundle

Export Markdown, a manifest, and explicitly selected artifacts under safe relative paths. Include schema version and SHA-256 checksums. Avoid absolute host paths. Re-import into an empty workspace and resolve exported references through the manifest mapping.

##### Acceptance and deliverables

Golden fixtures verify ordering, citations, redaction, unsupported claims, and deterministic non-LLM export. Round-trip a bundle and compare artifact hashes and relationships.

## M8-02 — Retrieval over prior writeups

### Goal and user-visible behavior

Find relevant prior techniques with source citations and explicit corpus boundaries.

#### Dependencies and owned files

Depends on M8-01 and artifact imports. Own `writeups/retrieval.py` and `features/retrieval/`.

##### M8-02a — Corpus ingestion

Start with user-imported writeups and permitted exports. Store source URI, title, content hash, license/permission metadata, imported timestamp, and visibility scope. Do not automatically scrape an entire external site. Split by headings with bounded overlapping text windows; store source character ranges.

##### M8-02b — Search and embeddings

Implement lexical search first. Add optional embeddings keyed by model ID, model version, normalization, chunk hash, and dimensions. Rebuild rather than mixing incompatible vectors. Respect the event's external-model policy during embedding generation. Never allow one competition's private corpus to appear in another without explicit sharing.

##### M8-02c — Results and context use

Return source excerpts, source ranges, score type, and provenance. Retrieved documents are untrusted reference data, not executable instructions. Selecting a result opens the source. Adding it to sidekick context requires an explicit selected reference and obeys context size limits.

##### Acceptance and deliverables

Test deleted sources, stale embeddings, cross-scope leakage, duplicate content, Unicode text, and no-network lexical operation. Show disabled embedding capability without breaking search.

## M8-03 — Evaluation harness and reproducibility

### Goal and user-visible behavior

Measure useful assistance and regressions on authorized, reproducible challenge fixtures.

#### Dependencies and owned files

Depends on jobs, sessions, evidence verification, and export manifests. Own `evaluation/runner.py`, `evaluation/metrics.py`, `tests/fixtures/evaluation/`, and report UI.

##### M8-03a — Benchmark manifest

Define `BenchmarkCase` with case ID, category, authorized source, artifact hashes, image digest, initial context, expected assertions, timeout, network policy, and permitted autonomy levels. Store expected answers outside agent context. Use small redistributable synthetic fixtures initially.

##### M8-03b — Isolated replay

Create fresh workspaces and sessions per case/run. Restore initial artifacts, pin tool images, and disable external submissions. Re-executing commands is distinct from rendering old events: label both modes explicitly. Agent outputs may vary; compare semantic assertions and evidence outcomes rather than exact prose.

##### M8-03c — Metric definitions

Record time from case start to first independently verified useful finding; proposal acceptance ratio with accepted/decided counts; refuted hypothesis ratio with reviewed population; tokens and estimated cost with missing-usage indicators; wall time; cancellation/failure counts; and solved cases. Do not label an unreviewed hypothesis as true or false. Human comparison reports must record participant count, task ordering, and model configuration.

##### M8-03d — Regression gates

Run deterministic fixture tests on tool changes. Run bounded agent benchmarks only when credentials, policy, and budget are configured. Fail on loss of required assertions, isolation breaches, or corrupted evidence. Report cost/latency changes without inventing significance from tiny samples.

##### Acceptance and deliverables

Two deterministic runs yield identical artifact hashes. A deliberately wrong agent claim does not satisfy the benchmark. Interrupted runs retain partial metrics and an explicit incomplete state.

# M9 — Long-tail tool coverage and optional capability packs

## M9-01 — Common capability-pack contract

### Goal and sequencing

Expand the design document's full tool catalog after core flows are stable. M9 is an implementation grouping for remaining scope, not a replacement for M1–M8. Each pack can be delegated independently after the shared tool registry and relevant viewer exist.

#### Atomic implementation requirements

Every tool must declare input/output schema, deterministic versus nondeterministic behavior, resource limits, network requirements, image/tool versions, output artifact types, cancellation behavior, and representative fixtures. Add UI forms through registry metadata and an optional custom viewer. Do not add placeholder buttons for missing capabilities.

##### M9-01a — Classical cipher pack

Own `tools/ciphers/`. Implement Affine, Beaufort, Autokey, Playfair, Two/Four-Square, Bifid/Trifid, ADFGX/ADFGVX, Hill, Rail Fence, Scytale, columnar/double transposition, Polybius, Nihilist, Bacon, and book-cipher operations as separate registry entries. For each specify alphabet, case preservation, padding, key validation, and treatment of non-alphabet symbols. Reject noninvertible Hill keys and invalid permutations. Publish round-trip and independent known-answer fixtures for each cipher; do not infer success solely from round trips.

##### M9-01b — Encoding and text pack

Own `tools/encodings/`. Add Base58/85/91, URL, HTML entities, Morse, Braille, NATO, semaphore notation, tap code, and A1Z26 with explicit alphabets/delimiters. Base58 variants require a named alphabet. Preserve bytes separately from text decoding. Add Brainfuck/Ook/Malbolge only as step-limited isolated interpreters with bounded memory/output, never host execution.

##### M9-01c — Mathematical and cryptanalysis pack

Own `tools/crypto/`. Implement GCD, modular inverse, CRT with consistency checks, base conversion, bounded factorization, XOR recovery, frequency/IoC/chi-squared scoring, and Vigenere key-length analysis. Return candidate scores, parameters, and source ranges; scores are not calibrated confidence. Wrap SageMath, z3, and RSA helper workflows in versioned capability images. Hashcat/john jobs require explicit workload limits and cancellation; passwords remain access controlled.

##### M9-01d — Binary and pwn pack

Own `tools/binary/` and `tools/pwn/`. Wrap checksec, cyclic generation/lookup, gadget listing, objdump, debugger scripting, and transcript-backed remote connections. Remote endpoints must pass the scope service. Dynamic tracing, Frida, angr, and execution of unknown samples use isolated runtime profiles. Tool output is parsed into structured records while retaining raw artifacts; unknown output formats fail visibly rather than returning empty success.

##### M9-01e — Disk, stego, and protocol pack

Own `tools/disk/`, `tools/stego/`, and `tools/network/`. Add archive/document extraction, Sleuth Kit inspection, carving, zsteg/steghide/stegseek, DTMF/Morse audio, exported network objects, DNS/HTTP summaries, USB HID decoding, and keylog-assisted TLS analysis. Bound expansion, file count, output bytes, and analysis duration. Avoid privileged host mounts; use read-only image parsers or a separately approved isolated VM workflow.

##### M9-01f — Web/OSINT and recipe pack

Own `tools/web/` and `tools/recipes/`. Route ffuf/sqlmap and browser helpers through explicit authorized scope and rate-limited jobs. External lookup providers require configured credentials and deliberate invocation; report unavailable providers honestly. A recipe is a versioned DAG of tool IDs, normalized parameters, and artifact references. Reject cycles, incompatible types, and missing versions before execution. CyberChef integration requires a pinned verified API adapter and parity fixtures; it must obey the same limits and provenance contract.

#### Completion gate

Maintain a capability matrix listing implemented, unavailable, and deferred tools with reasons. A pack is complete only when every advertised operation has a real implementation and acceptance fixture, and the UI and MCP invoke the identical operation through the shared execution service.


---
