from __future__ import annotations

import logging

import uvicorn

from ctf_workbench.config import get_settings


def main() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logging.getLogger(__name__).info("starting API %r", settings)
    uvicorn.run(
        "ctf_workbench.api.main:app",
        host=settings.bind_host,
        port=settings.bind_port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
