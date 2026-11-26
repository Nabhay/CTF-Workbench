# CTF Workbench

A local-first workspace for CTFs and cryptic hunts. You look at files, run tools, keep notes, and track leads in one place. Agents can help later; they never confirm a claim without you.

The workbench is the product. Manual solving works with no model credentials and no internet.

## Current status

**M0-01 is done:** a bootable FastAPI control plane, a worker process, and a React health screen that reports live API availability. Challenge workflows, the sandbox, and agents are not implemented yet.

| Milestone | Intent |
| --- | --- |
| M0 | Contracts, persistence, auth, events, sandbox/editor spike |
| M1 | Manual workbench: board, artifacts, toolbox, hex viewer, notebook, terminal, editor |
| M2 | Triage jobs and specialized viewers |
| M3–M5 | Sidekick, verification, delegated tasks |
| M6–M8 | Hunts, platforms, collaboration, writeups |

See `docs/execution/STATUS.md` for the live task ledger.

## Prerequisites

- **Python 3.11+** (developed on 3.14)
- **Node.js 20+**
- **uv** for Python environments and lockfiles
- **Windows** with Docker Desktop / WSL2, or **Linux**. Challenge tools will run in Linux containers (not required for M0-01).

## Setup

Install is separate from ordinary startup. Copy the example env, then install dependencies once.

```powershell
copy .env.example .env
# Edit .env and replace CTF_WORKBENCH_SESSION_SECRET with >= 32 random characters.

uv sync --group dev
npm --prefix apps/web install
```

Linux / macOS:

```bash
cp .env.example .env
uv sync --group dev
npm --prefix apps/web install
```

## Run

```powershell
.\scripts\dev.ps1
```

```bash
./scripts/dev.sh
```

The launcher checks prerequisites, binds to localhost, prints URLs, and on exit stops only the processes it started.

| Process | Default URL |
| --- | --- |
| API | http://127.0.0.1:8745/api/v1/health |
| UI | http://127.0.0.1:5173 |
| Worker | no HTTP port; `--check` exits after loading settings |

## Commands

| Action | Command |
| --- | --- |
| Backend install | `uv sync --group dev` |
| Frontend install | `npm --prefix apps/web install` |
| API | `uv run python -m ctf_workbench.api` |
| Worker | `uv run python -m ctf_workbench.jobs` |
| Worker check | `uv run python -m ctf_workbench.jobs --check` |
| Frontend dev | `npm --prefix apps/web run dev` |
| Frontend build | `npm --prefix apps/web run build` |
| Frontend typecheck | `npm --prefix apps/web run typecheck` |
| Unit / API tests | `uv run pytest` |
| Python lint | `uv run ruff check src tests` |
| Migrations | not yet (M0-02) |
| Integration / browser tests | not yet |

## Layout

```
src/ctf_workbench/     Python control plane (FastAPI, SQLAlchemy, tools, jobs)
apps/web/              React + Vite + Tailwind UI
scripts/               PowerShell and bash launchers
docs/execution/        Milestone specs and STATUS.md
data/                  Local DB, blobs, and challenge workspaces (gitignored)
```

Artifact bytes live under the configured data root, not in Git. Each challenge workspace will be its own Git repository under that root.

## Product rules

- Every mutation is attributed and logged. A claim without evidence stays visibly unsupported.
- Agents propose; humans accept. Confirmation is a separate click. Agents cannot confirm claims or approve flags.
- One tool implementation: the UI and MCP call the same service. The browser does not reimplement decoding.
- Untrusted execution happens in the sandbox. Host credentials and the Docker socket never enter challenge containers.
- Manual work stays available offline. If selected content is sent to a model, the UI will say so.

## Docs

- [Human-centric design](CTF%20Workbench%20Human-Centric%20Design%20Doc.md) — product intent
- [Execution plan](EXECUTION_PLAN.md) — implementation order and defaults
- [M0 foundation](docs/execution/01-foundation.md)
- [M1–M2 workbench](docs/execution/02-workbench.md)
- [M3–M5 agents](docs/execution/03-agents.md)
- [M6–M8 expansion](docs/execution/04-expansion.md)

This is not a portable `.exe`. Docker, Linux tool images, and any model runtime stay external prerequisites. Packaging an installer is a later deliverable.
