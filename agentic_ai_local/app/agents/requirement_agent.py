from __future__ import annotations
from app.schemas.requirement import Requirement, RequirementStep

def run(state: dict) -> dict:
    obs = state.get('observation') or {}; url = obs.get('detected_url')
    missing = [] if url else ["Base URL is required before DOM inspection can run."]
    steps = [RequirementStep(step_number=1, action='navigate', target_description='application URL', value=url)] if url else []
    if 'login' in state.get('user_prompt','').lower():
        steps += [RequirementStep(step_number=2, action='type', target_description='username field', value_from_env='APP_USERNAME'), RequirementStep(step_number=3, action='type', target_description='password field', value_from_env='APP_PASSWORD'), RequirementStep(step_number=4, action='click', target_description='login submit button'), RequirementStep(step_number=5, action='assert_text', target_description='dashboard confirmation text', expected_result='Dashboard')]
    req = Requirement(name='Local Selenium Automation', description=state.get('user_prompt',''), base_url=url, preconditions=['Ollama and target app are local'] if url else [], steps=steps, success_criteria=['All planned assertions pass'], missing_information=missing)
    return {"requirement": req.model_dump()}
