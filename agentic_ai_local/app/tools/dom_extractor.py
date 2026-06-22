from __future__ import annotations

import re

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
    if el.get('aria-label'): return f"//{el.name}[@aria-label='{el.get('aria-label')}']"
    text = el.get_text(' ', strip=True)
    if text and el.name in {"button", "a"}:
        return f"//{el.name}[normalize-space()='{text[:80]}']"
    return f"//{el.name}"


def _label_text(soup: BeautifulSoup, el) -> str | None:
    label_parts: list[str] = []
    element_id = el.get('id')
    if element_id:
        label = soup.find('label', attrs={'for': element_id})
        if label:
            label_parts.append(label.get_text(' ', strip=True))
    parent_label = el.find_parent('label')
    if parent_label:
        label_parts.append(parent_label.get_text(' ', strip=True))
    labelledby = el.get('aria-labelledby')
    if labelledby:
        for label_id in labelledby.split():
            node = soup.find(id=label_id)
            if node:
                label_parts.append(node.get_text(' ', strip=True))
    text = ' '.join(part for part in label_parts if part)
    return text[:120] or None


def _role(el) -> str:
    if el.get('role'):
        return el.get('role')
    if el.name == 'a':
        return 'link'
    if el.name == 'button' or (el.name == 'input' and (el.get('type') or '').lower() in {'button', 'submit', 'reset'}):
        return 'button'
    if el.name in {'input', 'textarea'}:
        return 'textbox' if (el.get('type') or 'text').lower() not in {'checkbox', 'radio'} else (el.get('type') or 'input').lower()
    if el.name == 'select':
        return 'combobox'
    return el.name


def _keywords(*parts: str | None) -> list[str]:
    words = re.findall(r"[a-z0-9]+", ' '.join(p or '' for p in parts).lower())
    stop = {'the', 'a', 'an', 'to', 'and', 'or', 'field', 'button', 'link', 'input', 'click', 'enter', 'type'}
    seen: set[str] = set()
    return [w for w in words if w not in stop and not (w in seen or seen.add(w))]


def summarize_html(url: str, html: str, title: str | None = None) -> dict:
    soup = BeautifulSoup(html, 'lxml')
    title = title or (soup.title.string if soup.title else None)

    def item(el):
        label = _label_text(soup, el)
        text = el.get_text(' ', strip=True)[:80] or None
        accessible_name = el.get('aria-label') or label or el.get('placeholder') or text or el.get('name') or el.get('id')
        return {
            "tag": el.name,
            "role": _role(el),
            "type": el.get('type'),
            "name": el.get('name'),
            "id": el.get('id'),
            "placeholder": el.get('placeholder'),
            "form_control_name": el.get('formcontrolname'),
            "aria_label": el.get('aria-label'),
            "label": label,
            "accessible_name": accessible_name,
            "text": text,
            "href": el.get('href'),
            "css_selector": _css(el),
            "xpath": _xpath(el),
            "keywords": _keywords(accessible_name, el.get('name'), el.get('id'), el.get('formcontrolname'), el.get('type')),
            "visible": True,
        }

    inputs = [item(e) for e in soup.find_all(['input', 'textarea', 'select'])[:75]]
    buttons = [item(e) for e in soup.find_all(['button'])[:75]]
    link_elements = [item(e) for e in soup.find_all('a')[:75]]
    data = {
        "url": url,
        "title": title,
        "forms": [],
        "inputs": inputs,
        "buttons": buttons,
        "links": [{"text": a.get("text"), "href": a.get("href"), "accessible_name": a.get("accessible_name"), "css_selector": a.get("css_selector"), "xpath": a.get("xpath"), "keywords": a.get("keywords", [])} for a in link_elements],
        "controls": inputs + buttons + link_elements,
        "page_text_sample": soup.get_text(' ', strip=True)[:1000],
        "errors": [],
    }
    raw = RUN_LOGS_DIR / f"dom_snapshot_{timestamp()}.html"; raw.write_text(html)
    summ = RUN_LOGS_DIR / f"dom_summary_{timestamp()}.json"; summ.write_text(dump_json(data))
    data["raw_html_file"] = relative_to_root(raw); data["summary_file"] = relative_to_root(summ)
    return data
