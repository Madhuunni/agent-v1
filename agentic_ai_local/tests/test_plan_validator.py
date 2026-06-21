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
