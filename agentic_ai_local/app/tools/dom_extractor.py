from __future__ import annotations
from bs4 import BeautifulSoup
from app.config import RUN_LOGS_DIR
from app.utils.paths import timestamp, relative_to_root
from app.utils.json_utils import dump_json

def _css(el) -> str:
    if el.get('data-testid'): return f"{el.name}[data-testid='{el.get('data-testid')}']"
    if el.get('id'): return f"#{el.get('id')}"
    if el.get('name'): return f"{el.name}[name='{el.get('name')}']"
    if el.get('formcontrolname'): return f"{el.name}[formcontrolname='{el.get('formcontrolname')}']"
    if el.get('aria-label'): return f"{el.name}[aria-label='{el.get('aria-label')}']"
    if el.get('placeholder'): return f"{el.name}[placeholder='{el.get('placeholder')}']"
    typ = el.get('type')
    return f"{el.name}[type='{typ}']" if typ else el.name

def _xpath(el) -> str:
    if el.get('id'): return f"//*[@id='{el.get('id')}']"
    if el.get('name'): return f"//{el.name}[@name='{el.get('name')}']"
    if el.get('formcontrolname'): return f"//{el.name}[@formcontrolname='{el.get('formcontrolname')}']"
    return f"//{el.name}"

def summarize_html(url: str, html: str, title: str | None = None) -> dict:
    soup = BeautifulSoup(html, 'lxml')
    title = title or (soup.title.string if soup.title else None)
    def item(el):
        return {"tag": el.name, "type": el.get('type'), "name": el.get('name'), "id": el.get('id'), "placeholder": el.get('placeholder'), "form_control_name": el.get('formcontrolname'), "aria_label": el.get('aria-label'), "text": el.get_text(' ', strip=True)[:80] or None, "css_selector": _css(el), "xpath": _xpath(el), "visible": True}
    data = {"url": url, "title": title, "forms": [], "inputs": [item(e) for e in soup.find_all('input')[:50]], "buttons": [item(e) for e in soup.find_all(['button'])[:50]], "links": [{"text": a.get_text(' ', strip=True)[:80], "href": a.get('href')} for a in soup.find_all('a')[:50]], "page_text_sample": soup.get_text(' ', strip=True)[:1000], "errors": []}
    raw = RUN_LOGS_DIR / f"dom_snapshot_{timestamp()}.html"; raw.write_text(html)
    summ = RUN_LOGS_DIR / f"dom_summary_{timestamp()}.json"; summ.write_text(dump_json(data))
    data["raw_html_file"] = relative_to_root(raw); data["summary_file"] = relative_to_root(summ)
    return data
