from __future__ import annotations
import requests
from app.tools.dom_extractor import summarize_html

def read_dom(url: str) -> dict:
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return summarize_html(url, resp.text)
    except Exception as exc:
        return {"url": url, "title": None, "forms": [], "inputs": [], "buttons": [], "links": [], "page_text_sample": "", "errors": [str(exc)]}
