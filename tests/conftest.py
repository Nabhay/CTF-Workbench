from __future__ import annotations

import os
import tempfile
from pathlib import Path

_TEST_ROOT = Path(tempfile.mkdtemp(prefix="ctf-workbench-test-"))
os.environ["CTF_WORKBENCH_SESSION_SECRET"] = "test-secret-not-for-production-use-ok"
os.environ["CTF_WORKBENCH_DATA_ROOT"] = str(_TEST_ROOT)
os.environ["CTF_WORKBENCH_DATABASE_URL"] = f"sqlite:///{_TEST_ROOT.as_posix()}/test.db"
os.environ["CTF_WORKBENCH_BIND_HOST"] = "127.0.0.1"
os.environ["CTF_WORKBENCH_BIND_PORT"] = "8745"
os.environ["CTF_WORKBENCH_ALLOW_NONLOCAL_BIND"] = "false"
