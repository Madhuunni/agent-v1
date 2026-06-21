from __future__ import annotations
import json, re
from typing import Any

def extract_json(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))

def dump_json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False, default=str)
