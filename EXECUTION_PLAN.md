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
