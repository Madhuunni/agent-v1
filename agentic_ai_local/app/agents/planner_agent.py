from __future__ import annotations
from app.graph.router import validate_plan
from app.llm.structured import invoke_json
from app.schemas.agent_plan import AgentPlan


def run(state: dict) -> dict:
    obs = state.get("observation") or {}
    prompt = state.get("user_prompt", "")
    plan = invoke_json(
        AgentPlan,
        "You are a planning agent. Convert the user request and observation into a minimal ordered specialist-agent JSON plan. Obey prerequisite order and use only allowed agent names.",
        {
            "user_prompt": prompt,
            "observation": obs,
            "limits": {
                "max_retries": state.get("max_retries", 2),
                "max_iterations": state.get("max_iterations", 8),
            },
        },
    )
    ok, errors, _ = validate_plan(plan.model_dump(), state)
    agent_outputs = {**state.get("agent_outputs", {})}
    if ok:
        seq = plan.agent_sequence
        if obs.get("requires_execution") and "executor_agent" not in seq:
            ok = False
            errors = ["Plan omits executor_agent even though observation requires execution"]
        elif obs.get("requires_code_generation") and "code_generator_agent" not in seq:
            ok = False
            errors = ["Plan omits code_generator_agent even though observation requires code generation"]
        elif obs.get("requires_dom_inspection") and "dom_agent" not in seq:
            ok = False
            errors = ["Plan omits dom_agent even though observation requires DOM inspection"]
    if not ok:
        return {
            "execution_plan": plan.model_dump(),
            "pending_agents": ["report_agent"],
            "agent_outputs": agent_outputs,
            "errors": state.get("errors", []) + [{"agent": "planner_agent", "error": "; ".join(errors)}],
        }
    return {
        "execution_plan": plan.model_dump(),
        "pending_agents": plan.agent_sequence,
        "max_retries": plan.max_retries,
        "max_iterations": plan.max_iterations,
        "agent_outputs": agent_outputs,
    }
