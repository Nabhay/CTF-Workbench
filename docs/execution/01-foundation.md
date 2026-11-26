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
