from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from app.config import RUN_LOGS_DIR
from app.utils.json_utils import dump_json
from app.utils.paths import timestamp

LOGGER = logging.getLogger("app.agent_calls")
LLM_LOGGER = logging.getLogger("app.llm")

_AGENT_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
_AGENT_LOG_SESSION = timestamp()
_AGENT_LOG_DIR = RUN_LOGS_DIR
_AGENT_FILE_HANDLERS: dict[str, logging.FileHandler] = {}
_AGENT_LOGGERS: dict[str, logging.Logger] = {}


def configure_agent_file_logging(
    *,
    log_dir: Path = RUN_LOGS_DIR,
    run_timestamp: str | None = None,
    verbose: bool = False,
) -> None:
    """Configure per-agent file logging for the current CLI run."""
    global _AGENT_LOG_SESSION, _AGENT_LOG_DIR

    close_agent_file_logging()
    _AGENT_LOG_DIR = Path(log_dir)
    _AGENT_LOG_DIR.mkdir(parents=True, exist_ok=True)
    _AGENT_LOG_SESSION = run_timestamp or timestamp()

    for logger in (*_AGENT_LOGGERS.values(), LOGGER, LLM_LOGGER):
        logger.setLevel(logging.DEBUG if verbose else logging.INFO)


def close_agent_file_logging() -> None:
    """Detach and close all per-agent file handlers."""
    for agent_name, handler in list(_AGENT_FILE_HANDLERS.items()):
        agent_logger = _AGENT_LOGGERS.get(agent_name)
        if agent_logger is not None:
            agent_logger.removeHandler(handler)
        handler.close()
    _AGENT_FILE_HANDLERS.clear()


_SCHEMA_LAYER_AGENT_NAMES = {
    "Observation": "observer_agent",
    "Requirement": "requirement_agent",
    "LocatorResult": "locator_agent",
    "TestPlan": "test_plan_agent",
}


def _base_agent_name(layer: str) -> str:
    first_segment = layer.split(".", 1)[0]
    return _SCHEMA_LAYER_AGENT_NAMES.get(
        first_segment,
        first_segment if first_segment.endswith("_agent") else layer,
    )


def _agent_file_prefix(agent_name: str) -> str:
    return _base_agent_name(agent_name).removesuffix("_agent")


def get_agent_log_path(agent_name: str) -> Path:
    """Return the per-agent log path for the active run."""
    return _AGENT_LOG_DIR / f"{_agent_file_prefix(agent_name)}_{_AGENT_LOG_SESSION}.log"


def _agent_logger(agent_name: str) -> logging.Logger:
    logger = _AGENT_LOGGERS.get(agent_name)
    if logger is None:
        logger = logging.getLogger(f"app.agent_calls.{agent_name}")
        logger.propagate = True
        logger.setLevel(LOGGER.level or logging.INFO)
        _AGENT_LOGGERS[agent_name] = logger

    if agent_name not in _AGENT_FILE_HANDLERS:
        _AGENT_LOG_DIR.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(get_agent_log_path(agent_name), encoding="utf-8")
        handler.setFormatter(logging.Formatter(_AGENT_LOG_FORMAT))
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        _AGENT_FILE_HANDLERS[agent_name] = handler

    return logger


def log_agent_start(agent_name: str, state: dict[str, Any]) -> None:
    logger = _agent_logger(agent_name)
    logger.info("[%s] agent call started", agent_name)
    logger.debug("[%s] state snapshot:\n%s", agent_name, dump_json(state))


def log_agent_end(agent_name: str, output: dict[str, Any]) -> None:
    logger = _agent_logger(agent_name)
    logger.info("[%s] agent call completed", agent_name)
    logger.debug("[%s] agent output:\n%s", agent_name, dump_json(output))


def log_agent_error(agent_name: str, exc: Exception) -> None:
    _agent_logger(agent_name).exception("[%s] agent call failed: %s", agent_name, exc)


def log_llm_request(layer: str, request_json: dict[str, Any]) -> None:
    agent_name = _base_agent_name(layer)
    _agent_logger(agent_name).info("[%s] LLM request JSON:\n%s", layer, dump_json(request_json))
    LLM_LOGGER.info("[%s] LLM request JSON:\n%s", layer, dump_json(request_json))


def log_llm_response(layer: str, response_json: dict[str, Any]) -> None:
    agent_name = _base_agent_name(layer)
    _agent_logger(agent_name).info("[%s] LLM response JSON:\n%s", layer, dump_json(response_json))
    LLM_LOGGER.info("[%s] LLM response JSON:\n%s", layer, dump_json(response_json))
