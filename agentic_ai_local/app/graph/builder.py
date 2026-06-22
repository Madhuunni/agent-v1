from __future__ import annotations
from langgraph.graph import END, StateGraph
from app.graph.state import AgentGraphState
from app.graph.nodes import observer_node, planner_node, router_node, make_agent_node
from app.graph.conditions import route_condition
from app.schemas.agent_plan import ALLOWED_AGENTS


def build_graph():
    """Build the prompt-to-report LangGraph workflow.

    The static edges perform the invariant setup work: observe the prompt, plan
    the agent sequence, then enter the router. Conditional edges from the router
    dispatch to whichever agent is currently selected in state. Every worker
    agent returns to the router until the report agent sets ``stop`` and the
    graph reaches END.
    """

    graph = StateGraph(AgentGraphState)

    # Bootstrap nodes: prompt interpretation and plan creation always happen
    # before dynamic routing begins.
    graph.add_node('observer_agent', observer_node)
    graph.add_node('planner_agent', planner_node)
    graph.add_node('router', router_node)

    # Register one graph node for every runnable specialist agent.
    for agent in ALLOWED_AGENTS:
        graph.add_node(agent, make_agent_node(agent))

    graph.set_entry_point('observer_agent')
    graph.add_edge('observer_agent', 'planner_agent')
    graph.add_edge('planner_agent', 'router')

    # The router writes ``current_agent``; this condition maps it to the next
    # node name or END when reporting has completed.
    graph.add_conditional_edges('router', route_condition, {**{a: a for a in ALLOWED_AGENTS}, '__end__': END})

    # Each specialist produces an artifact, then returns control to the router
    # so the next pending specialist can be selected.
    for agent in ALLOWED_AGENTS:
        graph.add_edge(agent, 'router')

    return graph.compile()
