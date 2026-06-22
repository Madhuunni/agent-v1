from __future__ import annotations
from app.graph.router import validate_plan
from app.llm.structured import invoke_json
from app.schemas.agent_plan import AgentPlan


def _fallback_plan(prompt: str, obs: dict, state: dict) -> AgentPlan:
    has_url = bool(obs.get("detected_url")); low = prompt.lower()
    browser_action_requested = any(w in low for w in ["navigate", "enter", "click", "login", "validate", "verify"])
    if has_url and (obs.get("requires_execution") or (obs.get("requires_code_generation") and browser_action_requested)):
        seq = [
            "requirement_agent",
            "dom_agent",
            "locator_agent",
            "test_plan_agent",
            "code_generator_agent",
            "code_validator_agent",
            "executor_agent",
            "report_agent",
        ]
        return AgentPlan(
            task_type=obs.get("task_type", "unknown"),
            goal=prompt,
            agent_sequence=seq,
            requires_browser=True,
            requires_code_generation=True,
            requires_execution=True,
            requires_debugging=False,
            max_retries=state.get("max_retries", 2),
            max_iterations=state.get("max_iterations", 8),
            risk_level="medium",
        )
    sequences = [
        (("fix", "debug", "failed"), ["executor_agent","debug_agent","code_generator_agent","code_validator_agent","executor_agent","report_agent"]),
        (("run", "execute"), ["requirement_agent","dom_agent","locator_agent","test_plan_agent","code_generator_agent","code_validator_agent","executor_agent","report_agent"]),
        (("generate", "code"), ["requirement_agent","dom_agent","locator_agent","test_plan_agent","code_generator_agent","code_validator_agent","report_agent"]),
        (("plan",), ["requirement_agent","dom_agent","locator_agent","test_plan_agent","report_agent"]),
        (("inspect",), ["dom_agent","report_agent"] if has_url else ["requirement_agent","report_agent"]),
    ]
    seq = next((s for keys, s in sequences if any(k in low for k in keys)), ["requirement_agent","report_agent"])
    if not has_url and any(a in seq for a in ("dom_agent", "locator_agent", "test_plan_agent", "code_generator_agent")):
        seq = ["requirement_agent", "report_agent"]
    return AgentPlan(task_type=obs.get("task_type","unknown"), goal=prompt, agent_sequence=seq, requires_browser="dom_agent" in seq, requires_code_generation="code_generator_agent" in seq, requires_execution="executor_agent" in seq, requires_debugging="debug_agent" in seq, max_retries=state.get("max_retries",2), max_iterations=state.get("max_iterations",8), risk_level="medium" if "executor_agent" in seq else "low")


def run(state: dict) -> dict:
    obs = state.get("observation") or {}; prompt = state.get("user_prompt", "")
    fallback = _fallback_plan(prompt, obs, state)
    plan, note = invoke_json(AgentPlan, "You are a planning agent. Convert the user request and observation into a minimal ordered specialist-agent JSON plan. Obey prerequisite order and use only allowed agent names.", {"user_prompt": prompt, "observation": obs, "limits": {"max_retries": state.get("max_retries", 2), "max_iterations": state.get("max_iterations", 8)}}, fallback)
    ok, errors, _ = validate_plan(plan.model_dump(), state)
    agent_outputs = {**state.get("agent_outputs", {})}
    if note:
        agent_outputs["planner_agent_llm_notes"] = note
    plan_errors = errors
    if ok:
        seq = plan.agent_sequence
        if obs.get("requires_execution") and "executor_agent" not in seq:
            ok = False
            plan_errors = ["Plan omits executor_agent even though observation requires execution"]
        elif obs.get("requires_code_generation") and "code_generator_agent" not in seq:
            ok = False
            plan_errors = ["Plan omits code_generator_agent even though observation requires code generation"]
        elif obs.get("requires_dom_inspection") and "dom_agent" not in seq:
            ok = False
            plan_errors = ["Plan omits dom_agent even though observation requires DOM inspection"]
    if not ok:
        fallback_ok, fallback_errors, _ = validate_plan(fallback.model_dump(), state)
        planner_error = {"agent": "planner_agent", "error": "; ".join(plan_errors)}
        if fallback_ok:
            agent_outputs["planner_agent_fallback_notes"] = "Local LLM plan failed validation or omitted required capabilities; continuing with deterministic fallback plan."
            return {
                "execution_plan": fallback.model_dump(),
                "pending_agents": fallback.agent_sequence,
                "max_retries": fallback.max_retries,
                "max_iterations": fallback.max_iterations,
                "agent_outputs": agent_outputs,
                "errors": state.get("errors", []) + [planner_error],
            }
        return {
            "execution_plan": fallback.model_dump(),
            "pending_agents": ["report_agent"],
            "agent_outputs": agent_outputs,
            "errors": state.get("errors", []) + [planner_error, {"agent": "planner_agent", "error": "Fallback plan failed validation: " + "; ".join(fallback_errors)}],
        }
    return {"execution_plan": plan.model_dump(), "pending_agents": plan.agent_sequence, "max_retries": plan.max_retries, "max_iterations": plan.max_iterations, "agent_outputs": agent_outputs}
