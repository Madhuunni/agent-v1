from __future__ import annotations
from app.llm.structured import invoke_json
from app.schemas.locator import LocatorResult


def run(state: dict) -> dict:
    req = state.get('requirement') or {}
    dom = state.get('dom_snapshot') or {}
    result = invoke_json(
        LocatorResult,
        "You are a locator agent. Match requirement steps to available DOM elements and return selected Selenium locators as JSON. Prefer id, then name, then css, then xpath.",
        {"requirement": req, "dom_snapshot": dom},
    )
    return {"selected_locators": result.model_dump(), "agent_outputs": {**state.get("agent_outputs", {})}}
