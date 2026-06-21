from __future__ import annotations
from pydantic import BaseModel, Field
class DebugResult(BaseModel):
    failure_summary: str
    likely_cause: str
    fix_strategy: str
    requires_dom_refresh: bool = False
    updated_steps: list[dict] = Field(default_factory=list)
    updated_locators: list[dict] = Field(default_factory=list)
    recommend_retry: bool = False
