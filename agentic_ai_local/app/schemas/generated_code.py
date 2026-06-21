from __future__ import annotations
from pydantic import BaseModel, Field
class GeneratedCode(BaseModel):
    file_path: str
    language: str = "python"
    framework: str = "selenium"
    summary: str
    requires_env: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
class CodeValidationResult(BaseModel):
    valid: bool
    file_path: str
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
