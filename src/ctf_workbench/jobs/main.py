from __future__ import annotations

import argparse
import logging
import signal
import time

from ctf_workbench.config import get_settings

logger = logging.getLogger("ctf_workbench.jobs")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CTF Workbench job worker")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Load settings, prove the process can start, and exit.",
    )
    args = parser.parse_args(argv)

    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logger.info("worker starting %r", settings)

    if args.check:
        logger.info("worker check ok; queue is not implemented yet (M0-05)")
        return 0

    stop = False

    def _handle_stop(signum: int, _frame: object) -> None:
        nonlocal stop
        logger.info("worker received signal %s; shutting down", signum)
        stop = True

    signal.signal(signal.SIGINT, _handle_stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handle_stop)

    logger.info("worker idle; waiting for jobs (none scheduled in M0-01)")
    while not stop:
        time.sleep(0.5)
    logger.info("worker stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
