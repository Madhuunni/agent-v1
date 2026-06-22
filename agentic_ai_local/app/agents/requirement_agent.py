from __future__ import annotations
from app.llm.structured import invoke_json
from app.llm.local_llm import get_chat_model
from app.schemas.requirement import Requirement, RequirementStep

def _fallback_requirement(prompt: str, url: str | None) -> Requirement:
    login_steps = [RequirementStep(step_number=2, action="type", target_description="username field", value_from_env="APP_USERNAME"), RequirementStep(step_number=3, action="type", target_description="password field", value_from_env="APP_PASSWORD"), RequirementStep(step_number=4, action="click", target_description="login submit button"), RequirementStep(step_number=5, action="assert_text", target_description="dashboard confirmation text", expected_result="Dashboard")]
    steps = [RequirementStep(step_number=1, action="navigate", target_description="application URL", value=url), *login_steps] if url else []
    return Requirement(name="Local Selenium Automation", description=prompt, base_url=url, preconditions=["Ollama and target app are local"] if url else [], steps=steps, success_criteria=["All planned assertions pass"], missing_information=[] if url else ["Base URL is required before DOM inspection can run."])

def _llm_notes(prompt: str, url: str | None) -> str | None:
    try:
        response = get_chat_model().invoke(
            "Return concise requirements-analysis notes for this local Selenium task. "
            f"Task: {prompt}\nBase URL: {url or 'missing'}"
        )
        return str(getattr(response, "content", response)).strip()
    except Exception as exc:
        return f"Local LLM unavailable; continuing with deterministic requirements. {exc}"

def run(state: dict) -> dict:
    obs = state.get("observation") or {}; prompt = state.get("user_prompt", ""); url = obs.get("detected_url")
    req, note = invoke_json(Requirement, "You are a requirements agent. Convert the prompt into ordered Selenium automation requirements. Use APP_USERNAME and APP_PASSWORD for login secrets. Include missing_information instead of guessing unavailable URLs.", {"user_prompt": prompt, "observation": obs}, _fallback_requirement(prompt, url))
    outputs = {**state.get("agent_outputs", {})}
    outputs["requirement_agent_llm_notes"] = _llm_notes(prompt, url) or note or ""
    return {"requirement": req.model_dump(), "agent_outputs": outputs}
