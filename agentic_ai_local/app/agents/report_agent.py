from __future__ import annotations
from app.utils.json_utils import dump_json


def run(state: dict) -> dict:
    """Assemble the terminal Markdown report from accumulated graph state.

    This is the final pipeline step. It deliberately reads from many optional
    artifacts because earlier planner decisions may skip DOM inspection, code
    generation, or execution. Missing sections are omitted; errors and missing
    information are surfaced so the caller knows what to provide or fix next.
    """

    obs = state.get('observation') or {}; plan = state.get('execution_plan') or {}
    lines = [f"# Local Agent Run Report", "", f"## User Request\n{state.get('user_prompt','')}", f"## Detected Task Type\n{obs.get('task_type','unknown')}", f"## Agents Executed\n{', '.join(state.get('completed_agents', [])) or 'None'}", "## Plan", '```json', dump_json(plan), '```']
    llm_notes = (state.get("agent_outputs") or {}).get("requirement_agent_llm_notes")
    if llm_notes:
        lines += ["## Local LLM Notes", llm_notes]
    if state.get('dom_snapshot'):
        lines += ["## Browser DOM Inspection", f"- URL: {state['dom_snapshot'].get('url')}", f"- Browser: {state['dom_snapshot'].get('browser', 'unknown')}"]
        if state['dom_snapshot'].get('screenshot'):
            lines.append(f"- Screenshot: {state['dom_snapshot']['screenshot']}")
    if state.get('generated_code'): lines += ["## Generated Files", f"- {state['generated_code']['file_path']}"]
    if state.get('execution_result'): lines += ["## Execution Status", f"- Success: {state['execution_result']['success']}", f"- Log: {state['execution_result']['log_file']}"]
    missing_information = list((state.get('requirement') or {}).get('missing_information') or [])
    execution_result = state.get('execution_result') or {}
    # A successful run means the generated script had enough information to complete.
    # Local LLM requirement notes can still contain stale asks (for example, asking
    # for selectors even after DOM inspection/execution succeeded), so suppress those
    # contradictions from the final user-facing report.
    if execution_result.get('success') is True:
        missing_information = []
    if missing_information: lines += ["## Missing Information", *[f"- {m}" for m in missing_information]]
    if state.get('errors'): lines += ["## Errors", '```json', dump_json(state['errors']), '```']
    recommendation = "Review the generated artifacts. Chrome DOM inspection and execution artifacts above show what ran locally."
    needs_browser_target = any(
        obs.get(flag)
        for flag in ("requires_dom_inspection", "requires_code_generation", "requires_execution")
    )
    has_browser_artifacts = bool(state.get('dom_snapshot') or state.get('execution_result'))
    detected_url = obs.get('detected_url')
    if needs_browser_target and not detected_url and not has_browser_artifacts:
        recommendation = "Provide a reachable http:// or https:// URL and rerun so Chrome can navigate to the target application."
    elif state.get('errors'):
        recommendation = "Review the errors above, update the request or local environment, and rerun when ready."
    lines += ["## Retry Attempts", str(state.get('retry_count',0)), "## Final Recommendation", recommendation]
    return {"final_report": '\n'.join(lines), "stop": True}
