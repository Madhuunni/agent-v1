from __future__ import annotations
import re
from app.memory.memory_store import load_memory
from app.schemas.agent_plan import ALLOWED_AGENTS
from app.schemas.observation import Observation
from app.config import GENERATED_TESTS_DIR, RUN_LOGS_DIR

def _detect_url(prompt: str) -> str | None:
    # Accept both valid URLs (http://localhost:4200) and the common typo
    # reported by users (http:/localhost:4200), then normalize before any
    # browser or generated Selenium code sees it.
    url = next(iter(re.findall(r"https?:/{1,2}\S+", prompt)), None)
    if not url:
        return None
    url = url.rstrip('.,;:!?)\"\'')
    return re.sub(r"^(https?):/([^/])", r"\1://\2", url)

def run(state: dict) -> dict:
    prompt = state.get('user_prompt','')
    url = _detect_url(prompt)
    low = prompt.lower()
    obs = Observation(user_goal=prompt, task_type="selenium_test_generation" if "selenium" in low or "test" in low else "browser_inspection", detected_url=url, requires_dom_inspection=bool(url and any(w in low for w in ['inspect','page','dom','selenium','test'])), requires_code_generation="generate" in low and ("code" in low or "selenium" in low or "test" in low), requires_execution=any(w in low for w in ['run','execute']), requires_debugging=any(w in low for w in ['fix','debug','failed']), available_agents=sorted(ALLOWED_AGENTS), available_tools=["browser_dom_reader","selenium_runner","file_writer","python_syntax_checker"], known_context=load_memory(), existing_generated_tests=[p.name for p in GENERATED_TESTS_DIR.glob('*.py')], existing_run_logs=[p.name for p in RUN_LOGS_DIR.glob('*')], risks=[])
    return {"observation": obs.model_dump()}
