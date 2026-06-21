from app.schemas.agent_plan import AgentPlan
from app.schemas.requirement import Requirement, RequirementStep
from app.schemas.execution import ExecutionResult

def test_planner_output_schema():
    plan = AgentPlan(task_type="selenium", goal="g", agent_sequence=["report_agent"])
    assert plan.agent_sequence == ["report_agent"]

def test_requirement_schema():
    req = Requirement(name="n", description="d", steps=[RequirementStep(step_number=1, action="navigate", target_description="url")])
    assert req.steps[0].action == "navigate"

def test_execution_result_schema():
    result = ExecutionResult(success=True, exit_code=0, log_file="run_logs/x.log", duration_seconds=0.1)
    assert result.success
