from __future__ import annotations
from pydantic import BaseModel, Field

class Observation(BaseModel):
    user_goal: str
    task_type: str
    detected_url: str | None = None
    requires_dom_inspection: bool = False
    requires_code_generation: bool = False
    requires_execution: bool = False
    requires_debugging: bool = False
    available_agents: list[str] = Field(default_factory=list)
    available_tools: list[str] = Field(default_factory=list)
    known_context: dict = Field(default_factory=dict)
    existing_generated_tests: list[str] = Field(default_factory=list)
    existing_run_logs: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
