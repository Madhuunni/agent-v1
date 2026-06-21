from __future__ import annotations
from app.schemas.agent_plan import ALLOWED_AGENTS

def route_condition(state: dict) -> str:
    current = state.get('current_agent')
    if not current or state.get('stop'):
        return "__end__"
    return current if current in ALLOWED_AGENTS else "report_agent"
