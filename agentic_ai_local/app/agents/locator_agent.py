from __future__ import annotations
import re

from app.llm.structured import invoke_json
from app.schemas.locator import LocatorChoice, LocatorResult

_ACTIONLESS = {'navigate','assert_text','assert_url','wait','screenshot'}

def _candidate_locators(el: dict) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    form_control_name = el.get("form_control_name")
    form_control_css = f"{el.get('tag') or '*'}[formcontrolname='{form_control_name}']" if form_control_name else None
    form_control_xpath = f"//{el.get('tag') or '*'}[@formcontrolname='{form_control_name}']" if form_control_name else None
    pairs = [
        ("id", el.get("id")),
        ("name", el.get("name")),
        ("css", form_control_css),
        ("css", el.get("css_selector")),
        ("xpath", form_control_xpath),
        ("xpath", el.get("xpath")),
    ]
    for by, target in pairs:
        if target and {"by": by, "target": target} not in candidates:
            candidates.append({"by": by, "target": target})
    for raw in el.get("candidate_selectors") or []:
        by = raw.get("by")
        target = raw.get("target")
        if by in {"id", "name", "css", "xpath"} and target and {"by": by, "target": target} not in candidates:
            candidates.append({"by": by, "target": target})
    return candidates

def _best(el: dict) -> tuple[str, str | None]:
    candidates = _candidate_locators(el)
    return (candidates[0]["by"], candidates[0]["target"]) if candidates else ("css", None)

def _tokens(text: str) -> set[str]:
    stop = {'the', 'a', 'an', 'to', 'and', 'or', 'field', 'button', 'link', 'input', 'click', 'enter', 'type', 'select'}
    return {w for w in re.findall(r'[a-z0-9]+', text.lower()) if w not in stop}

def _element_text(el: dict) -> str:
    fields = ['accessible_name', 'label', 'name', 'id', 'placeholder', 'form_control_name', 'aria_label', 'text', 'type', 'role']
    return ' '.join(str(el.get(f) or '') for f in fields)

def _score(step: dict, el: dict) -> int:
    step_tokens = _tokens(step.get('target_description', ''))
    element_tokens = set(el.get('keywords') or []) | _tokens(_element_text(el))
    score = len(step_tokens & element_tokens) * 10
    action = step.get('action')
    role = (el.get('role') or '').lower()
    tag = (el.get('tag') or '').lower()
    if action == 'click' and (role in {'button', 'link'} or tag in {'button', 'a'}):
        score += 5
    if action == 'type' and tag in {'input', 'textarea'}:
        score += 5
    if action == 'select' and tag == 'select':
        score += 5
    return score

def _fallback(req: dict, dom: dict) -> LocatorResult:
    pool = dom.get('controls') or (dom.get('inputs', []) + dom.get('buttons', []) + dom.get('links', []))
    locators, missing = [], []
    warnings = []
    for step in [s for s in req.get('steps', []) if s.get('action') not in _ACTIONLESS]:
        scored = sorted(((_score(step, el), el) for el in pool), key=lambda item: item[0], reverse=True)
        element = scored[0][1] if scored and scored[0][0] > 0 else None
        if element is None:
            missing.append(step.get('target_description', 'unknown target')); continue
        candidates = _candidate_locators(element)
        by, locator = _best(element)
        fallbacks = [candidate for candidate in candidates if candidate != {'by': by, 'target': locator}]
        locators.append(LocatorChoice(step_number=step['step_number'], target_description=step['target_description'], selected_by=by, selected_locator=locator or '', confidence=0.9 if scored[0][0] >= 15 else 0.7, reason='Selected from navigated DOM control inventory matched against prompt wording and available input/button metadata', fallback_locators=fallbacks).model_dump())
    if not dom.get('controls'):
        warnings.append('DOM snapshot did not include controls inventory; used legacy inputs/buttons/links pools.')
    return LocatorResult(locators=locators, missing_targets=missing, warnings=warnings)

def run(state: dict) -> dict:
    req = state.get('requirement') or {}; dom = state.get('dom_snapshot') or {}
    result, note = invoke_json(LocatorResult, "You are a locator agent. Match requirement steps to available DOM elements and return selected Selenium locators as JSON. Prefer id, then name, then css, then xpath.", {"requirement": req, "dom_snapshot": dom}, _fallback(req, dom))
    outputs = {**state.get("agent_outputs", {})}
    if note: outputs["locator_agent_llm_notes"] = note
    return {"selected_locators": result.model_dump(), "agent_outputs": outputs}
