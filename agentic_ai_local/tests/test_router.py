from app.graph.nodes import AGENT_RUNNERS, make_agent_node
from app.graph.router import after_agent, route_next
from app.utils.json_utils import dump_json

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


def test_agent_node_does_not_create_circular_agent_output(monkeypatch):
    monkeypatch.setitem(AGENT_RUNNERS, "report_agent", lambda state: {"final_report": "ok", "stop": True})
    node = make_agent_node("report_agent")

    updates = node({"completed_agents": [], "errors": [], "pending_agents": [], "agent_outputs": {}})

    assert updates["agent_outputs"]["report_agent"] == {"final_report": "ok", "stop": True}
    assert updates["agent_outputs"]["report_agent"] is not updates
    dump_json(updates)
