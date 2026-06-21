from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field

Action = Literal["navigate","click","type","select","assert_text","assert_url","wait","screenshot"]
class RequirementStep(BaseModel):
    step_number: int
    action: Action
    target_description: str
    value: str | None = None
    value_from_env: str | None = None
    expected_result: str | None = None
class Requirement(BaseModel):
    name: str
    description: str
    base_url: str | None = None
    preconditions: list[str] = Field(default_factory=list)
    steps: list[RequirementStep] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
