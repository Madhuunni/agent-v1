from __future__ import annotations
from app.llm.structured import invoke_json
from app.schemas.locator import LocatorChoice, LocatorResult

_ACTIONLESS = {'navigate','assert_text','assert_url','wait','screenshot'}

def _best(el: dict) -> tuple[str, str | None]:
    pairs = [("id", el.get("id")), ("name", el.get("name")), ("css", el.get("css_selector")), ("xpath", el.get("xpath"))]
    return next(((k, v) for k, v in pairs if v), ("css", None))

def _fallback(req: dict, dom: dict) -> LocatorResult:
    pool = dom.get('inputs', []) + dom.get('buttons', [])
    locators, missing = [], []
    for step in [s for s in req.get('steps', []) if s.get('action') not in _ACTIONLESS]:
        keys = step.get('target_description', '').lower().split()
        element = next((el for el in pool if any(k in ' '.join(str(el.get(f) or '') for f in ['name','id','placeholder','aria_label','text','type']).lower() for k in keys)), None)
        if element is None:
            missing.append(step.get('target_description', 'unknown target')); continue
        by, locator = _best(element)
        locators.append(LocatorChoice(step_number=step['step_number'], target_description=step['target_description'], selected_by=by, selected_locator=locator or '', confidence=0.85, reason='Selected from DOM element attributes', fallback_locators=[element.get('xpath','')]).model_dump())
    return LocatorResult(locators=locators, missing_targets=missing, warnings=[])

def run(state: dict) -> dict:
    req = state.get('requirement') or {}; dom = state.get('dom_snapshot') or {}
    result, note = invoke_json(LocatorResult, "You are a locator agent. Match requirement steps to available DOM elements and return selected Selenium locators as JSON. Prefer id, then name, then css, then xpath.", {"requirement": req, "dom_snapshot": dom}, _fallback(req, dom))
    outputs = {**state.get("agent_outputs", {})}
    if note: outputs["locator_agent_llm_notes"] = note
    return {"selected_locators": result.model_dump(), "agent_outputs": outputs}
