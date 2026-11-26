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
