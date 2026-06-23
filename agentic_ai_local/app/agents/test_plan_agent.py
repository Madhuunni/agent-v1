from __future__ import annotations
from app.llm.structured import invoke_json
from app.schemas.test_plan import TestPlan


def run(state: dict) -> dict:
    req = state.get('requirement') or {}
    selected = state.get('selected_locators') or {}
    plan = invoke_json(
        TestPlan,
        "You are a test-plan agent. Convert requirements and selected locators into executable Selenium TestStep JSON. Do not invent locators.",
        {"requirement": req, "selected_locators": selected},
    )
    return {"test_plan": plan.model_dump(), "agent_outputs": {**state.get("agent_outputs", {})}}
