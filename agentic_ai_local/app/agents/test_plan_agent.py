from __future__ import annotations
from app.schemas.test_plan import TestPlan, TestStep

def run(state: dict) -> dict:
    req = state.get('requirement') or {}; locs = {l['step_number']: l for l in (state.get('selected_locators') or {}).get('locators', [])}
    steps=[]
    for s in req.get('steps', []):
        if s['action']=='navigate': steps.append(TestStep(action='navigate', target=s.get('value') or req.get('base_url') or '', description='Navigate to application').model_dump()); continue
        if s['action']=='assert_text': steps.append(TestStep(action='assert_text', by='body', target=s.get('expected_result') or s['target_description'], description='Verify expected text').model_dump()); continue
        loc = locs.get(s['step_number'])
        if loc: steps.append(TestStep(action=s['action'], by=loc['selected_by'], target=loc['selected_locator'], value=s.get('value'), value_from_env=s.get('value_from_env'), description=s['target_description']).model_dump())
    plan = TestPlan(name=req.get('name','Generated Selenium Test'), base_url=req.get('base_url'), steps=steps, assertions=[], warnings=[])
    return {"test_plan": plan.model_dump()}
