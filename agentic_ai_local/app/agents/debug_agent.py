from __future__ import annotations
from app.llm.structured import invoke_json
from app.schemas.report import DebugResult

def _fallback_debug(ex: dict) -> DebugResult:
    text = (ex.get('stderr') or ex.get('stdout') or '').lower()
    causes = {"timeout": "timeout", "no such element": "selector_not_found", "app_password": "auth_failure", "app_username": "auth_failure", "driver": "browser_error"}
    cause = next((v for k, v in causes.items() if k in text), "unknown")
    return DebugResult(failure_summary=ex.get('stderr','Execution failed')[:500], likely_cause=cause, fix_strategy='Review selectors, environment variables, and local browser availability before retrying.', requires_dom_refresh=cause=='selector_not_found', recommend_retry=cause in {'selector_not_found','timeout'})

def run(state: dict) -> dict:
    ex = state.get('execution_result') or {}
    dbg, note = invoke_json(DebugResult, "You are a debugging agent. Classify the Selenium execution failure and return a structured JSON retry recommendation.", {"execution_result": ex, "errors": state.get("errors", [])}, _fallback_debug(ex))
    outputs = {**state.get("agent_outputs", {})}
    if note: outputs["debug_agent_llm_notes"] = note
    return {"debug_result": dbg.model_dump(), "agent_outputs": outputs}
