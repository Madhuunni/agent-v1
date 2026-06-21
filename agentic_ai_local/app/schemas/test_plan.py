from __future__ import annotations
from pydantic import BaseModel, Field
class TestStep(BaseModel):
    action: str
    by: str | None = None
    target: str
    value: str | None = None
    value_from_env: str | None = None
    description: str
class TestPlan(BaseModel):
    name: str
    base_url: str | None = None
    steps: list[TestStep] = Field(default_factory=list)
    assertions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
