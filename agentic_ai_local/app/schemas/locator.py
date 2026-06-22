from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field

class LocatorCandidate(BaseModel):
    by: Literal["css","xpath","id","name"]
    target: str
class LocatorChoice(BaseModel):
    step_number: int
    target_description: str
    selected_by: Literal["css","xpath","id","name"]
    selected_locator: str
    confidence: float = Field(ge=0, le=1)
    reason: str
    fallback_locators: list[LocatorCandidate] = Field(default_factory=list)
class LocatorResult(BaseModel):
    locators: list[LocatorChoice] = Field(default_factory=list)
    missing_targets: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
