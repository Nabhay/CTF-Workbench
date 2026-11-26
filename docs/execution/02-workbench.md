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

