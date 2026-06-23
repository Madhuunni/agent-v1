from __future__ import annotations
from app.llm.structured import invoke_json
from app.llm.local_llm import get_chat_model
from app.utils.agent_logging import log_llm_request, log_llm_response
from app.schemas.requirement import Requirement

def _llm_notes(prompt: str, url: str | None) -> str | None:
    request_json = {"task": prompt, "base_url": url}
    log_llm_request("requirement_agent.notes", request_json)
    try:
        response = get_chat_model().invoke(
            "Return concise requirements-analysis notes for this local Selenium task. "
            f"Task: {prompt}\nBase URL: {url or 'missing'}"
        )
        content = str(getattr(response, "content", response)).strip()
        log_llm_response("requirement_agent.notes", {"raw": content})
        return content
    except Exception as exc:
        log_llm_response("requirement_agent.notes", {"error": str(exc)})
        raise

def run(state: dict) -> dict:
    obs = state.get("observation") or {}; prompt = state.get("user_prompt", ""); url = obs.get("detected_url")
    req = invoke_json(Requirement, "You are a requirements agent. Convert the prompt into ordered Selenium automation requirements. Use APP_USERNAME and APP_PASSWORD for login secrets. Include missing_information instead of guessing unavailable URLs.", {"user_prompt": prompt, "observation": obs})
    outputs = {**state.get("agent_outputs", {})}
    outputs["requirement_agent_llm_notes"] = _llm_notes(prompt, url) or ""
    return {"requirement": req.model_dump(), "agent_outputs": outputs}
