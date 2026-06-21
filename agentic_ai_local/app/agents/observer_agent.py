from __future__ import annotations
import re
from app.memory.memory_store import load_memory
from app.schemas.agent_plan import ALLOWED_AGENTS
from app.schemas.observation import Observation
from app.config import GENERATED_TESTS_DIR, RUN_LOGS_DIR

def run(state: dict) -> dict:
    prompt = state.get('user_prompt','')
    url = next(iter(re.findall(r"https?://\S+", prompt)), None)
    if url:
        url = url.rstrip('.,;:!?)\"\'')
    low = prompt.lower()
    obs = Observation(user_goal=prompt, task_type="selenium_test_generation" if "selenium" in low or "test" in low else "browser_inspection", detected_url=url, requires_dom_inspection=bool(url and any(w in low for w in ['inspect','page','dom','selenium','test'])), requires_code_generation="generate" in low and ("code" in low or "selenium" in low or "test" in low), requires_execution=any(w in low for w in ['run','execute']), requires_debugging=any(w in low for w in ['fix','debug','failed']), available_agents=sorted(ALLOWED_AGENTS), available_tools=["browser_dom_reader","selenium_runner","file_writer","python_syntax_checker"], known_context=load_memory(), existing_generated_tests=[p.name for p in GENERATED_TESTS_DIR.glob('*.py')], existing_run_logs=[p.name for p in RUN_LOGS_DIR.glob('*')], risks=[])
    return {"observation": obs.model_dump()}
