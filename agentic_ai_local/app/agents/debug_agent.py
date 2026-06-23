from __future__ import annotations
from app.llm.structured import invoke_json
from app.schemas.report import DebugResult

def run(state: dict) -> dict:
    ex = state.get('execution_result') or {}
    dbg = invoke_json(DebugResult, "You are a debugging agent. Classify the Selenium execution failure and return a structured JSON retry recommendation.", {"execution_result": ex, "errors": state.get("errors", [])})
    return {"debug_result": dbg.model_dump(), "agent_outputs": {**state.get("agent_outputs", {})}}
