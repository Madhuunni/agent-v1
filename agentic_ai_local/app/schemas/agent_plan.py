from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field

ALLOWED_AGENTS = {"requirement_agent","dom_agent","locator_agent","test_plan_agent","code_generator_agent","code_validator_agent","executor_agent","debug_agent","report_agent"}

class AgentPlan(BaseModel):
    task_type: str
    goal: str
    agent_sequence: list[str] = Field(min_length=1)
    parallel_agents: list[str] = Field(default_factory=list)
    requires_browser: bool = False
    requires_code_generation: bool = False
    requires_execution: bool = False
    requires_debugging: bool = False
    max_retries: int = Field(default=2, ge=0, le=5)
    max_iterations: int = Field(default=8, ge=1, le=15)
    stop_condition: str = "report_agent completed"
    risk_level: Literal["low","medium","high"] = "low"
    notes: list[str] = Field(default_factory=list)
