import pytest


def test_agent_modules_do_not_expose_private_fallback_functions():
    from app.agents import debug_agent, locator_agent, observer_agent, planner_agent, requirement_agent, test_plan_agent

    for module in [debug_agent, locator_agent, observer_agent, planner_agent, requirement_agent, test_plan_agent]:
        assert not any(name.startswith("_fallback") for name in vars(module))


def test_structured_invoke_json_raises_when_llm_unavailable(monkeypatch):
    from app.llm import structured
    from app.llm.local_llm import OllamaUnavailableError
    from app.schemas.report import DebugResult

    def unavailable_model():
        raise OllamaUnavailableError("ollama is offline")

    monkeypatch.setattr(structured, "get_chat_model", unavailable_model)

    with pytest.raises(OllamaUnavailableError):
        structured.invoke_json(
            DebugResult,
            "Return debug JSON.",
            {"execution_result": {}, "errors": []},
        )
