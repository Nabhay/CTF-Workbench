# Task ledger

Statuses: `pending`, `claimed`, `in_progress`, `blocked`, `review`, `done`.
A prior `done` is evidence to inspect, not a reason to recreate a feature.

## M0 — Foundation and contracts

| ID | Status | Owner | Dependencies | Files | Validation evidence | Blocker |
| --- | --- | --- | --- | --- | --- | --- |
| M0-01 | done | integrator | none | `pyproject.toml`, `uv.lock`, `src/ctf_workbench/**`, `apps/web/**`, `scripts/**`, `README.md` | `uv run pytest` 6 passed; `uv run ruff check src tests` clean; `npm --prefix apps/web run build` succeeded (Vite 7.3.8); `uv run python -m ctf_workbench.jobs --check` exited 0; `GET /api/v1/health` returned `status=ok`; health UI showed live bind `127.0.0.1:8745`; short session secret raised an actionable ValidationError | |
| M0-02 | done | integrator | M0-01 | `src/ctf_workbench/db/`, `alembic/`, `src/ctf_workbench/services/events.py` | `uv run pytest` 18 passed including WAL/FK pragmas, upgrade-to-head, close/reopen, invalid FK, CAS 409, state+event rollback, monotonic event seq, local-admin bootstrap | |
| M0-03 | done | integrator | M0-02 | `api/events.py`, `services/outbox.py`, `api/ws.py`, `features/health/EventStream.tsx` | pytest event history/outbox/WS; origin 1008; client dedupes event IDs; reconnect uses after_seq | Cookie session auth for streams lands in M0-04 |
| M0-04 | in_progress | integrator | M0-02 | API errors, refs, session, OpenAPI | error envelope done; ResourceRef resolve in progress | |
| M0-05 | pending | integrator | M0-02, M0-04 | tool runs, jobs, policy | | |
| M0-06 | pending | integrator | M0-01, M0-04 | sandbox/editor spike | Docker Desktop required for the live spike | |
| M0-07 | pending | integrator | M0-01–M0-06 | freeze contracts | | |

## M1–M8

Not claimed. See `docs/execution/02-workbench.md`, `03-agents.md`, and `04-expansion.md`.
