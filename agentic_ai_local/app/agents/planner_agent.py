from __future__ import annotations
from app.graph.router import validate_plan
from app.schemas.agent_plan import AgentPlan

def _sequence(prompt: str, obs: dict) -> list[str]:
    low = prompt.lower(); has_url = bool(obs.get('detected_url'))
    if any(w in low for w in ['fix','debug','failed']): return ["executor_agent","debug_agent","code_generator_agent","code_validator_agent","executor_agent","report_agent"]
    if "existing" in low and any(w in low for w in ['run','execute']): return ["executor_agent","report_agent"]
    if not has_url and any(w in low for w in ['dom','selenium','test','page']): return ["requirement_agent","report_agent"]
    if "inspect" in low and "test" not in low and "generate" not in low: return ["dom_agent","report_agent"]
    if "plan" in low and "code" not in low and not any(w in low for w in ['run','execute']): return ["requirement_agent","dom_agent","locator_agent","test_plan_agent","report_agent"]
    if any(w in low for w in ['run','execute']): return ["requirement_agent","dom_agent","locator_agent","test_plan_agent","code_generator_agent","code_validator_agent","executor_agent","report_agent"]
    if "generate" in low or "code" in low: return ["requirement_agent","dom_agent","locator_agent","test_plan_agent","code_generator_agent","code_validator_agent","report_agent"]
    return ["requirement_agent","report_agent"]

def run(state: dict) -> dict:
    obs = state.get('observation') or {}; prompt = state.get('user_prompt','')
    seq = _sequence(prompt, obs)
    plan = AgentPlan(task_type=obs.get('task_type','unknown'), goal=prompt, agent_sequence=seq, requires_browser='dom_agent' in seq, requires_code_generation='code_generator_agent' in seq, requires_execution='executor_agent' in seq, requires_debugging='debug_agent' in seq, max_retries=state.get('max_retries',2), max_iterations=state.get('max_iterations',8), risk_level='medium' if 'executor_agent' in seq else 'low', notes=[])
    ok, errors, _ = validate_plan(plan.model_dump(), state)
    if not ok:
        return {"execution_plan": plan.model_dump(), "pending_agents": ["report_agent"], "errors": state.get('errors', []) + [{"agent":"planner_agent","error":"; ".join(errors)}]}
    return {"execution_plan": plan.model_dump(), "pending_agents": seq, "max_retries": plan.max_retries, "max_iterations": plan.max_iterations}
