from __future__ import annotations
from app.tools.selenium_runner import run_generated_script
from app.schemas.execution import ExecutionResult

def run(state: dict) -> dict:
    file_path = (state.get('generated_code') or {}).get('file_path') or 'generated_tests/login_and_verify_dashboard.py'
    result = ExecutionResult.model_validate(run_generated_script(file_path)).model_dump()
    updates = {"execution_result": result}
    if not result['success']:
        updates['errors'] = state.get('errors', []) + [{"agent":"executor_agent","error":result.get('stderr') or 'execution failed'}]
    return updates
