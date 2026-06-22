from __future__ import annotations
import json
import re
from typing import Any, TypeVar
from pydantic import BaseModel, ValidationError
from app.llm.local_llm import get_chat_model

T = TypeVar('T', bound=BaseModel)

def _text(message: Any) -> str:
    return str(getattr(message, 'content', message)).strip()

def extract_json(text: str) -> str:
    text = text.strip()
    if text.startswith('{') and text.endswith('}'):
        return text
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return fenced.group(1)
    first, last = text.find('{'), text.rfind('}')
    if first != -1 and last > first:
        return text[first:last + 1]
    raise ValueError('No JSON object found in local LLM output')

def invoke_json(schema: type[T], system: str, payload: dict[str, Any], fallback: T) -> tuple[T, str | None]:
    """Ask the local LLM for one JSON object matching a Pydantic schema.

    Agents use this to keep their run functions data-driven. When Ollama is not
    available or produces invalid JSON, the provided schema-valid fallback keeps
    CLI/tests deterministic while surfacing the reason as a note.
    """
    prompt = (
        f"{system}\n\nReturn only valid JSON matching this schema. No markdown.\n"
        f"Schema: {json.dumps(schema.model_json_schema(), indent=2)}\n\n"
        f"Input JSON: {json.dumps(payload, indent=2, default=str)}"
    )
    try:
        response = get_chat_model().invoke(prompt)
        data = json.loads(extract_json(_text(response)))
        return schema.model_validate(data), None
    except (Exception, ValidationError) as exc:
        return fallback, f"Local LLM JSON unavailable; used schema fallback. {exc}"
