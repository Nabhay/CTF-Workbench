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
