from __future__ import annotations

from app.llm.local_llm import get_chat_model
from app.schemas.requirement import Requirement, RequirementStep


def _local_llm_notes(prompt: str, url: str | None) -> str:
    try:
        model = get_chat_model()
        response = model.invoke(
            "You are a local Selenium requirements analyst. "
            "Return a concise checklist of requirements and risks for this task. "
            "Do not recommend cloud services.\n\n"
            f"Task: {prompt}\nBase URL: {url or 'missing'}"
        )
        return str(getattr(response, "content", response)).strip()
    except Exception as exc:
        return f"Local LLM unavailable; continuing with deterministic requirements. {exc}"


def run(state: dict) -> dict:
    obs = state.get('observation') or {}; url = obs.get('detected_url')
    missing = [] if url else ["Base URL is required before DOM inspection can run."]
    steps = [RequirementStep(step_number=1, action='navigate', target_description='application URL', value=url)] if url else []
    if 'login' in state.get('user_prompt','').lower():
        steps += [RequirementStep(step_number=2, action='type', target_description='username field', value_from_env='APP_USERNAME'), RequirementStep(step_number=3, action='type', target_description='password field', value_from_env='APP_PASSWORD'), RequirementStep(step_number=4, action='click', target_description='login submit button'), RequirementStep(step_number=5, action='assert_text', target_description='dashboard confirmation text', expected_result='Dashboard')]
    llm_notes = _local_llm_notes(state.get('user_prompt',''), url)
    req = Requirement(name='Local Selenium Automation', description=state.get('user_prompt',''), base_url=url, preconditions=['Ollama and target app are local'] if url else [], steps=steps, success_criteria=['All planned assertions pass'], missing_information=missing)
    return {"requirement": req.model_dump(), "agent_outputs": {**state.get("agent_outputs", {}), "requirement_agent_llm_notes": llm_notes}}
