from __future__ import annotations
from app.tools.browser_tool import read_dom

def run(state: dict) -> dict:
    url = (state.get('requirement') or {}).get('base_url') or (state.get('observation') or {}).get('detected_url')
    if not url: raise ValueError('DOM inspection requires a base URL')
    return {"dom_snapshot": read_dom(url)}
