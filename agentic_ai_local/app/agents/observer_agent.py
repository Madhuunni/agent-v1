from __future__ import annotations
from app.memory.memory_store import load_memory
from app.schemas.agent_plan import ALLOWED_AGENTS
from app.schemas.observation import Observation
from app.config import GENERATED_TESTS_DIR, RUN_LOGS_DIR
from app.llm.structured import invoke_json

def run(state: dict) -> dict:
    prompt = state.get('user_prompt','')
    obs = invoke_json(Observation, "You are an observation agent. Convert the raw prompt and local context into structured JSON facts for a Selenium automation graph.", {"user_prompt": prompt, "known_context": load_memory(), "existing_generated_tests": [p.name for p in GENERATED_TESTS_DIR.glob('*.py')], "existing_run_logs": [p.name for p in RUN_LOGS_DIR.glob('*')], "available_agents": sorted(ALLOWED_AGENTS)})
    return {"observation": obs.model_dump(), "agent_outputs": {**state.get("agent_outputs", {})}}
