import pytest
from pydantic import ValidationError

from app.schemas.agent_plan import AgentPlan
from app.schemas.execution import ExecutionResult
from app.schemas.requirement import Requirement, RequirementStep
from app.schemas.test_plan import TestPlan as SeleniumTestPlan, TestStep as SeleniumTestStep


def test_planner_output_schema():
    plan = AgentPlan(task_type="selenium", goal="g", agent_sequence=["report_agent"])
    assert plan.agent_sequence == ["report_agent"]


def test_requirement_schema():
    req = Requirement(name="n", description="d", steps=[RequirementStep(step_number=1, action="navigate", target_description="url")])
    assert req.steps[0].action == "navigate"


def test_execution_result_schema():
    result = ExecutionResult(success=True, exit_code=0, log_file="run_logs/x.log", duration_seconds=0.1)
    assert result.success


def test_test_plan_rejects_locator_as_navigation_url():
    with pytest.raises(ValidationError):
        SeleniumTestStep(action="navigate", target="//body", description="Invalid navigation")


def test_test_plan_requires_absolute_http_base_url():
    with pytest.raises(ValidationError):
        SeleniumTestPlan(name="bad base", base_url="localhost:4200")
