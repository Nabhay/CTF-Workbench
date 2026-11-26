from __future__ import annotations

from ctf_workbench.jobs.main import main


def test_worker_check_exits_cleanly() -> None:
    assert main(["--check"]) == 0
