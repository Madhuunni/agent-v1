from app.graph.router import route_next, after_agent

def test_executes_pending_agents_in_order():
    state = {"pending_agents":["a","b"], "iteration_count":0}
    nxt = route_next(state)
    assert nxt["current_agent"] == "a"
    assert nxt["pending_agents"] == ["b"]

def test_stops_when_pending_agents_empty_with_report_done():
    nxt = route_next({"pending_agents":[], "final_report":"done"})
    assert nxt["stop"] is True

def test_routes_to_report_agent_on_error():
    updates = after_agent({"pending_agents":["x"], "errors":[], "completed_agents":[], "max_retries":0}, "dom_agent", error=RuntimeError("boom"))
    assert updates["pending_agents"] == ["report_agent"]
    assert updates["errors"]
