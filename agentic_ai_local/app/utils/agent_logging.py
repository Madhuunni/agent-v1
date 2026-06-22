from __future__ import annotations
import logging
from typing import Any
from app.utils.json_utils import dump_json

LOGGER = logging.getLogger("app.agent_calls")
LLM_LOGGER = logging.getLogger("app.llm")


def log_agent_start(agent_name: str, state: dict[str, Any]) -> None:
    LOGGER.info("[%s] agent call started", agent_name)
    LOGGER.debug("[%s] state snapshot:\n%s", agent_name, dump_json(state))


def log_agent_end(agent_name: str, output: dict[str, Any]) -> None:
    LOGGER.info("[%s] agent call completed", agent_name)
    LOGGER.debug("[%s] agent output:\n%s", agent_name, dump_json(output))


def log_agent_error(agent_name: str, exc: Exception) -> None:
    LOGGER.exception("[%s] agent call failed: %s", agent_name, exc)


def log_llm_request(layer: str, request_json: dict[str, Any]) -> None:
    LLM_LOGGER.info("[%s] LLM request JSON:\n%s", layer, dump_json(request_json))


def log_llm_response(layer: str, response_json: dict[str, Any]) -> None:
    LLM_LOGGER.info("[%s] LLM response JSON:\n%s", layer, dump_json(response_json))
