from __future__ import annotations
import re
from app.memory.memory_store import load_memory
from app.schemas.agent_plan import ALLOWED_AGENTS
from app.schemas.observation import Observation
from app.config import GENERATED_TESTS_DIR, RUN_LOGS_DIR
from app.llm.structured import invoke_json

def _detect_url(prompt: str) -> str | None:
    url = next(iter(re.findall(r"https?:/{1,2}\S+", prompt)), None)
    return re.sub(r"^(https?):/([^/])", r"\1://\2", url.rstrip('.,;:!?)\"\'')) if url else None

def _fallback_observation(prompt: str) -> Observation:
    low = prompt.lower(); url = _detect_url(prompt)
    return Observation(user_goal=prompt, task_type="selenium_test_generation" if any(w in low for w in ["selenium", "test"]) else "browser_inspection", detected_url=url, requires_dom_inspection=bool(url and any(w in low for w in ["inspect","page","dom","selenium","test"])), requires_code_generation=any(w in low for w in ["generate", "code", "selenium", "test"]), requires_execution=any(w in low for w in ["run","execute"]), requires_debugging=any(w in low for w in ["fix","debug","failed"]), available_agents=sorted(ALLOWED_AGENTS), available_tools=["browser_dom_reader","selenium_runner","file_writer","python_syntax_checker"], known_context=load_memory(), existing_generated_tests=[p.name for p in GENERATED_TESTS_DIR.glob('*.py')], existing_run_logs=[p.name for p in RUN_LOGS_DIR.glob('*')], risks=[])

def run(state: dict) -> dict:
    prompt = state.get('user_prompt','')
    obs, note = invoke_json(Observation, "You are an observation agent. Convert the raw prompt and local context into structured JSON facts for a Selenium automation graph.", {"user_prompt": prompt, "known_context": load_memory(), "existing_generated_tests": [p.name for p in GENERATED_TESTS_DIR.glob('*.py')], "existing_run_logs": [p.name for p in RUN_LOGS_DIR.glob('*')], "available_agents": sorted(ALLOWED_AGENTS)}, _fallback_observation(prompt))
    outputs = {**state.get("agent_outputs", {})}
    if note: outputs["observer_agent_llm_notes"] = note
    return {"observation": obs.model_dump(), "agent_outputs": outputs}
