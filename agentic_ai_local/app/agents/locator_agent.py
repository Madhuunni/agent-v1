from __future__ import annotations
from app.schemas.locator import LocatorChoice, LocatorResult

def _match(desc: str, dom: dict) -> dict | None:
    pool = dom.get('inputs', []) + dom.get('buttons', [])
    keys = desc.lower().split()
    for el in pool:
        text = ' '.join(str(el.get(k) or '') for k in ['name','id','placeholder','aria_label','text','type']).lower()
        if any(k in text for k in keys): return el
    return pool[0] if pool else None

def run(state: dict) -> dict:
    req = state.get('requirement') or {}; dom = state.get('dom_snapshot') or {}
    choices=[]; missing=[]
    for step in req.get('steps', []):
        if step['action'] in ['navigate','assert_text','assert_url','wait','screenshot']: continue
        el = _match(step['target_description'], dom)
        if not el: missing.append(step['target_description']); continue
        by = 'css'; locator = el.get('css_selector')
        if el.get('id'): by='id'; locator=el['id']
        elif el.get('name'): by='name'; locator=el['name']
        choices.append(LocatorChoice(step_number=step['step_number'], target_description=step['target_description'], selected_by=by, selected_locator=locator, confidence=0.85, reason='Selected stable available attribute', fallback_locators=[el.get('xpath','')]).model_dump())
    return {"selected_locators": LocatorResult(locators=choices, missing_targets=missing, warnings=[]).model_dump()}
