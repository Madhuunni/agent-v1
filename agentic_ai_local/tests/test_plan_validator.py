from app.graph.router import validate_plan

def base(seq):
    return {"task_type":"t","goal":"g","agent_sequence":seq,"max_retries":2,"max_iterations":8,"stop_condition":"done","risk_level":"low"}

def test_rejects_unknown_agents():
    ok, errors, _ = validate_plan(base(["bad_agent","report_agent"]), {})
    assert not ok and any("Unknown" in e for e in errors)

def test_rejects_invalid_dependencies():
    ok, errors, _ = validate_plan(base(["locator_agent","report_agent"]), {})
    assert not ok and any("locator_agent requires" in e for e in errors)

def test_accepts_valid_sequence():
    ok, errors, _ = validate_plan(base(["requirement_agent","dom_agent","locator_agent","test_plan_agent","report_agent"]), {})
    assert ok, errors



def test_planner_reports_invalid_llm_plan_without_fallback(monkeypatch):
    from app.agents import planner_agent
    from app.schemas.agent_plan import AgentPlan

    bad_plan = AgentPlan(
        task_type="Test Generation and Execution",
        goal="Generate and run Selenium login test for http://localhost:4200",
        agent_sequence=[
            "requirement_agent",
            "dom_agent",
            "locator_agent",
            "code_generator_agent",
            "test_plan_agent",
            "code_validator_agent",
            "executor_agent",
            "report_agent",
        ],
        requires_browser=True,
        requires_code_generation=True,
        requires_execution=True,
        risk_level="medium",
    )

    monkeypatch.setattr(planner_agent, "invoke_json", lambda schema, system, payload: bad_plan)

    result = planner_agent.run(
        {
            "user_prompt": "Generate and run Selenium login test for http://localhost:4200",
            "observation": {"task_type": "Test Generation and Execution", "detected_url": "http://localhost:4200"},
            "max_retries": 2,
            "max_iterations": 8,
        }
    )

    assert result["pending_agents"] == ["report_agent"]
    assert any("code_generator_agent requires" in item["error"] for item in result["errors"])
    assert "planner_agent_fallback_notes" not in result["agent_outputs"]
