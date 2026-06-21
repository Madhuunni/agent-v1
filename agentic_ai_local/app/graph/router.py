from __future__ import annotations
from typing import Any
from app.schemas.agent_plan import ALLOWED_AGENTS, AgentPlan

ROUTER_NODE = "router"

def validate_plan(plan_data: dict[str, Any], state: dict[str, Any]) -> tuple[bool, list[str], AgentPlan | None]:
    errors: list[str] = []
    try:
        plan = AgentPlan.model_validate(plan_data)
    except Exception as exc:
        return False, [f"Plan schema validation failed: {exc}"], None
    seq = plan.agent_sequence
    if not seq:
        errors.append("agent_sequence must not be empty")
    unknown = [a for a in seq if a not in ALLOWED_AGENTS]
    if unknown:
        errors.append(f"Unknown agents: {unknown}")
    if len(seq) > plan.max_iterations:
        errors.append("Sequence length exceeds max_iterations")
    if plan.max_iterations < 1 or plan.max_iterations > 15:
        errors.append("max_iterations must be between 1 and 15")
    if plan.max_retries < 0 or plan.max_retries > 5:
        errors.append("max_retries must be between 0 and 5")
    prior = set()
    for agent in seq:
        if agent == "locator_agent" and "dom_agent" not in prior and not state.get("selected_locators"):
            errors.append("locator_agent requires dom_agent before it unless selected_locators exists")
        if agent == "test_plan_agent" and "requirement_agent" not in prior and not state.get("requirement"):
            errors.append("test_plan_agent requires requirement_agent before it unless requirement exists")
        if agent == "code_generator_agent" and "test_plan_agent" not in prior and not state.get("test_plan"):
            errors.append("code_generator_agent requires test_plan_agent before it unless test_plan exists")
        if agent == "code_validator_agent" and "code_generator_agent" not in prior and not state.get("generated_code"):
            errors.append("code_validator_agent requires code_generator_agent before it unless generated_code exists")
        if agent == "executor_agent" and not (state.get("generated_code") or "code_generator_agent" in prior or "existing" in state.get("user_prompt", "").lower()):
            errors.append("executor_agent requires generated_code unless running an existing script")
        prior.add(agent)
    if seq and seq[-1] != "report_agent":
        errors.append("report_agent should be final")
    return not errors, errors, plan

def route_next(state: dict[str, Any]) -> dict[str, Any]:
    if state.get("stop"):
        return {"current_agent": None}
    pending = list(state.get("pending_agents", []))
    if not pending:
        return {"current_agent": "report_agent", "pending_agents": []} if not state.get("final_report") else {"current_agent": None, "stop": True}
    current = pending.pop(0)
    return {"current_agent": current, "pending_agents": pending, "iteration_count": state.get("iteration_count", 0) + 1}

def after_agent(state: dict[str, Any], agent_name: str, output: Any = None, error: Exception | None = None) -> dict[str, Any]:
    completed = list(state.get("completed_agents", []))
    errors = list(state.get("errors", []))
    pending = list(state.get("pending_agents", []))
    updates: dict[str, Any] = {"completed_agents": completed, "errors": errors, "pending_agents": pending}
    if error:
        errors.append({"agent": agent_name, "error": str(error)})
        if agent_name == "executor_agent" and state.get("retry_count", 0) < state.get("max_retries", 0):
            updates["retry_count"] = state.get("retry_count", 0) + 1
            updates["pending_agents"] = ["debug_agent", "code_generator_agent", "code_validator_agent", "executor_agent", "report_agent"]
        else:
            updates["pending_agents"] = ["report_agent"]
    else:
        completed.append(agent_name)
        agent_outputs = dict(state.get("agent_outputs", {}))
        agent_outputs[agent_name] = output
        updates["agent_outputs"] = agent_outputs
    return updates
