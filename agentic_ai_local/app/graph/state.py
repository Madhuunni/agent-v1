from __future__ import annotations
from typing import Any, TypedDict


class AgentGraphState(TypedDict, total=False):
    """Shared state passed between every LangGraph node.

    Each agent reads the fields it depends on and returns a partial update.
    LangGraph merges those updates into this state, which lets the router move
    the run from the original prompt through requirements, DOM inspection, code
    generation, execution, debugging, and final report generation.
    """

    # Raw user input and first-pass prompt interpretation.
    user_prompt: str
    observation: dict[str, Any] | None

    # Planner/router fields that decide which agent runs next.
    execution_plan: dict[str, Any] | None
    pending_agents: list[str]
    completed_agents: list[str]
    current_agent: str | None
    agent_outputs: dict[str, Any]

    # Pipeline artifacts produced one stage at a time.
    requirement: dict[str, Any] | None
    dom_snapshot: dict[str, Any] | None
    selected_locators: dict[str, Any] | None
    test_plan: dict[str, Any] | None
    generated_code: dict[str, Any] | None
    code_validation_result: dict[str, Any] | None
    execution_result: dict[str, Any] | None
    debug_result: dict[str, Any] | None
    final_report: str | None

    # Safety and termination controls.
    errors: list[dict[str, Any]]
    retry_count: int
    max_retries: int
    max_iterations: int
    iteration_count: int
    stop: bool


def initial_state(user_prompt: str, max_retries: int = 2, max_iterations: int = 8) -> AgentGraphState:
    """Create the starting state for a prompt-driven graph invocation.

    The prompt is the only required user input. All later fields start empty so
    each agent can make its responsibility explicit by filling exactly the
    artifact it owns.
    """

    return {
        "user_prompt": user_prompt,
        "observation": None,
        "execution_plan": None,
        "pending_agents": [],
        "completed_agents": [],
        "current_agent": None,
        "agent_outputs": {},
        "requirement": None,
        "dom_snapshot": None,
        "selected_locators": None,
        "test_plan": None,
        "generated_code": None,
        "code_validation_result": None,
        "execution_result": None,
        "debug_result": None,
        "final_report": None,
        "errors": [],
        "retry_count": 0,
        "max_retries": max_retries,
        "max_iterations": max_iterations,
        "iteration_count": 0,
        "stop": False,
    }
