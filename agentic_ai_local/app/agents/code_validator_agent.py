from __future__ import annotations
from pathlib import Path
from app.config import ROOT_DIR
from app.schemas.generated_code import CodeValidationResult
from app.tools.python_validator import validate_python_file

def run(state: dict) -> dict:
    file_path = (state.get('generated_code') or {}).get('file_path')
    if not file_path: raise ValueError('No generated code to validate')
    ok, errors, warnings = validate_python_file(ROOT_DIR / file_path)
    return {"code_validation_result": CodeValidationResult(valid=ok, file_path=file_path, errors=errors, warnings=warnings).model_dump(), "errors": state.get('errors', []) + ([{"agent":"code_validator_agent","error":"; ".join(errors)}] if errors else [])}
