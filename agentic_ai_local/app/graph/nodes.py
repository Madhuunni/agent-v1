from __future__ import annotations
from app.agents import observer_agent, planner_agent, requirement_agent, dom_agent, locator_agent, test_plan_agent, code_generator_agent, code_validator_agent, executor_agent, debug_agent, report_agent
from app.graph.router import route_next, after_agent

AGENT_RUNNERS = {"requirement_agent": requirement_agent.run, "dom_agent": dom_agent.run, "locator_agent": locator_agent.run, "test_plan_agent": test_plan_agent.run, "code_generator_agent": code_generator_agent.run, "code_validator_agent": code_validator_agent.run, "executor_agent": executor_agent.run, "debug_agent": debug_agent.run, "report_agent": report_agent.run}

def observer_node(state: dict) -> dict: return observer_agent.run(state)
def planner_node(state: dict) -> dict: return planner_agent.run(state)
def router_node(state: dict) -> dict: return route_next(state)

def make_agent_node(agent_name: str):
    def node(state: dict) -> dict:
        try:
            output = AGENT_RUNNERS[agent_name](state)
            merged = dict(state); merged.update(output)
            after = after_agent(merged, agent_name, output=output)
            output.update(after)
            return output
        except Exception as exc:
            return after_agent(state, agent_name, error=exc)
    return node
