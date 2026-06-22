from __future__ import annotations
from app.llm.structured import invoke_json
from app.schemas.test_plan import TestPlan, TestStep

def _valid_locator_candidates(candidates: list[dict]) -> list[dict[str, str]]:
    valid: list[dict[str, str]] = []
    for candidate in candidates or []:
        by = candidate.get('by')
        target = candidate.get('target')
        if by in {'id', 'name', 'css', 'xpath'} and isinstance(target, str) and target.strip():
            item = {'by': by, 'target': target.strip()}
            if item not in valid:
                valid.append(item)
    return valid

def _fallback(req: dict, selected: dict) -> TestPlan:
    locs = {l['step_number']: l for l in selected.get('locators', []) if l.get('selected_locator')}
    builders = {
        'navigate': lambda s: TestStep(action='navigate', target=s.get('value') or req.get('base_url') or '', description='Navigate to application').model_dump(),
        'assert_text': lambda s: TestStep(action='assert_text', by='body', target=s.get('expected_result') or s['target_description'], description='Verify expected text').model_dump(),
    }
    steps = []
    for s in req.get('steps', []):
        loc = locs.get(s['step_number'])
        build = builders.get(s['action'])
        item = build(s) if build else (TestStep(action=s['action'], by=loc['selected_by'], target=loc['selected_locator'], value=s.get('value'), value_from_env=s.get('value_from_env'), description=s['target_description'], locator_candidates=_valid_locator_candidates(loc.get('fallback_locators', []))).model_dump() if loc else None)
        if item: steps.append(item)
    return TestPlan(name=req.get('name','Generated Selenium Test'), base_url=req.get('base_url'), steps=steps, assertions=[], warnings=[])

def run(state: dict) -> dict:
    req = state.get('requirement') or {}; selected = state.get('selected_locators') or {}
    plan, note = invoke_json(TestPlan, "You are a test-plan agent. Convert requirements and selected locators into executable Selenium TestStep JSON. Do not invent locators.", {"requirement": req, "selected_locators": selected}, _fallback(req, selected))
    outputs = {**state.get("agent_outputs", {})}
    if note: outputs["test_plan_agent_llm_notes"] = note
    return {"test_plan": plan.model_dump(), "agent_outputs": outputs}
