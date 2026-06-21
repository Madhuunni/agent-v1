from __future__ import annotations
from app.config import MEMORY_FILE
from app.utils.json_utils import dump_json
import json

def load_memory() -> dict:
    if not MEMORY_FILE.exists():
        return {"known_urls": [], "successful_selectors": {}, "failed_selectors": {}, "generated_tests": [], "execution_results": []}
    return json.loads(MEMORY_FILE.read_text())

def save_memory(memory: dict) -> None:
    MEMORY_FILE.parent.mkdir(exist_ok=True)
    MEMORY_FILE.write_text(dump_json(memory))

def remember_successful_selector(url: str, target_description: str, locator: str) -> None:
    mem = load_memory(); mem.setdefault("successful_selectors", {}).setdefault(url, {})[target_description] = locator; save_memory(mem)

def remember_failed_selector(url: str, locator: str, error: str) -> None:
    mem = load_memory(); mem.setdefault("failed_selectors", {}).setdefault(url, []).append({"locator": locator, "error": error}); save_memory(mem)

def get_known_selectors(url: str) -> dict:
    return load_memory().get("successful_selectors", {}).get(url, {})
