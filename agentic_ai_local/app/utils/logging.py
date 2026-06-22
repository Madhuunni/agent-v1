from __future__ import annotations

import logging

from app.config import RUN_LOGS_DIR
from app.utils.agent_logging import configure_agent_file_logging
from app.utils.paths import timestamp


def configure_logging(verbose: bool = False) -> None:
    run_timestamp = timestamp()
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    configure_agent_file_logging(
        log_dir=RUN_LOGS_DIR,
        run_timestamp=run_timestamp,
        verbose=verbose,
    )
