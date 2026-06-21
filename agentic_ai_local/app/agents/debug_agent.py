from __future__ import annotations
from app.schemas.report import DebugResult

def run(state: dict) -> dict:
    ex = state.get('execution_result') or {}; text = (ex.get('stderr') or ex.get('stdout') or '').lower()
    cause = 'timeout' if 'timeout' in text else 'selector_not_found' if 'no such element' in text else 'auth_failure' if 'app_password' in text or 'app_username' in text else 'browser_error' if 'driver' in text else 'unknown'
    dbg = DebugResult(failure_summary=ex.get('stderr','Execution failed')[:500], likely_cause=cause, fix_strategy='Review selectors, environment variables, and local browser availability before retrying.', requires_dom_refresh=cause=='selector_not_found', recommend_retry=cause in {'selector_not_found','timeout'})
    return {"debug_result": dbg.model_dump()}
