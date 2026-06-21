from __future__ import annotations
from pydantic import BaseModel, Field
class ExecutionResult(BaseModel):
    success: bool
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    log_file: str
    screenshots: list[str] = Field(default_factory=list)
    duration_seconds: float
    error_type: str | None = None
