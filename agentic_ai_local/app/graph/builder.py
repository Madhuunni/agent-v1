from __future__ import annotations
from langgraph.graph import END, StateGraph
from app.graph.state import AgentGraphState
from app.graph.nodes import observer_node, planner_node, router_node, make_agent_node
from app.graph.conditions import route_condition
from app.schemas.agent_plan import ALLOWED_AGENTS

def build_graph():
    graph = StateGraph(AgentGraphState)
    graph.add_node('observer_agent', observer_node)
    graph.add_node('planner_agent', planner_node)
    graph.add_node('router', router_node)
    for agent in ALLOWED_AGENTS:
        graph.add_node(agent, make_agent_node(agent))
    graph.set_entry_point('observer_agent')
    graph.add_edge('observer_agent', 'planner_agent')
    graph.add_edge('planner_agent', 'router')
    graph.add_conditional_edges('router', route_condition, {**{a:a for a in ALLOWED_AGENTS}, '__end__': END})
    for agent in ALLOWED_AGENTS:
        graph.add_edge(agent, 'router')
    return graph.compile()
