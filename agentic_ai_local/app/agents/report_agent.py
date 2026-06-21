from __future__ import annotations
from app.utils.json_utils import dump_json

def run(state: dict) -> dict:
    obs = state.get('observation') or {}; plan = state.get('execution_plan') or {}
    lines = [f"# Local Agent Run Report", "", f"## User Request\n{state.get('user_prompt','')}", f"## Detected Task Type\n{obs.get('task_type','unknown')}", f"## Agents Executed\n{', '.join(state.get('completed_agents', [])) or 'None'}", "## Plan", '```json', dump_json(plan), '```']
    if state.get('generated_code'): lines += ["## Generated Files", f"- {state['generated_code']['file_path']}"]
    if state.get('execution_result'): lines += ["## Execution Status", f"- Success: {state['execution_result']['success']}", f"- Log: {state['execution_result']['log_file']}"]
    if (state.get('requirement') or {}).get('missing_information'): lines += ["## Missing Information", *[f"- {m}" for m in state['requirement']['missing_information']]]
    if state.get('errors'): lines += ["## Errors", '```json', dump_json(state['errors']), '```']
    lines += ["## Retry Attempts", str(state.get('retry_count',0)), "## Final Recommendation", "Review the generated artifacts and run locally with Ollama plus the target application available."]
    return {"final_report": '\n'.join(lines), "stop": True}
