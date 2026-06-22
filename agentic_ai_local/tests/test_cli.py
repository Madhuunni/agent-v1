from typer.testing import CliRunner

from app import cli as cli_module


runner = CliRunner()


def test_run_command_accepts_headless_boolean_value(monkeypatch, tmp_path):
    captured = {}

    class FakeGraph:
        def invoke(self, state):
            captured["state"] = state
            return {"final_report": "ok"}

    monkeypatch.setattr(cli_module, "build_graph", lambda: FakeGraph())
    monkeypatch.setattr(cli_module, "get_settings", lambda: None)
    monkeypatch.setattr(
        cli_module,
        "configure_logging",
        lambda verbose: captured.setdefault("verbose", verbose),
    )
    monkeypatch.setattr(cli_module, "RUN_LOGS_DIR", tmp_path)

    result = runner.invoke(
        cli_module.cli,
        [
            "run",
            "Generate and run Selenium login test for http://localhost:4200",
            "--max-retries",
            "2",
            "--headless",
            "true",
            "--verbose",
        ],
    )

    assert result.exit_code == 0, result.output
    assert captured["verbose"] is True
    assert cli_module.os.environ["HEADLESS"] == "true"
    assert (
        captured["state"]["user_prompt"]
        == "Generate and run Selenium login test for http://localhost:4200"
    )


def test_observer_strips_trailing_prompt_punctuation_from_url():
    from app.agents import observer_agent

    result = observer_agent.run(
        {"user_prompt": 'Generate Selenium test for http://localhost:4200).'}
    )

    assert result["observation"]["detected_url"] == "http://localhost:4200"


def test_observer_normalizes_single_slash_localhost_url():
    from app.agents import observer_agent

    result = observer_agent.run(
        {"user_prompt": "Generate and run Selenium login test for http:/localhost:4200"}
    )

    assert result["observation"]["detected_url"] == "http://localhost:4200"


def test_requirement_agent_invokes_local_llm(monkeypatch):
    from app.agents import requirement_agent

    calls = []

    class FakeModel:
        def invoke(self, prompt):
            calls.append(prompt)
            return type("Response", (), {"content": "local llm checklist"})()

    monkeypatch.setattr(requirement_agent, "get_chat_model", lambda: FakeModel())

    result = requirement_agent.run(
        {
            "user_prompt": "Generate and run Selenium login test for http://localhost:4200",
            "observation": {"detected_url": "http://localhost:4200"},
            "agent_outputs": {},
        }
    )

    assert calls
    assert result["agent_outputs"]["requirement_agent_llm_notes"] == "local llm checklist"


def test_requirement_agent_continues_when_local_llm_unavailable(monkeypatch):
    from app.agents import requirement_agent
    from app.llm.local_llm import OllamaUnavailableError

    def unavailable_model():
        raise OllamaUnavailableError("ollama is offline")

    monkeypatch.setattr(requirement_agent, "get_chat_model", unavailable_model)

    result = requirement_agent.run(
        {
            "user_prompt": "Generate Selenium test plan",
            "observation": {"detected_url": None},
            "agent_outputs": {},
        }
    )

    assert result["requirement"]["missing_information"] == [
        "Base URL is required before DOM inspection can run."
    ]
    assert (
        "continuing with deterministic requirements"
        in result["agent_outputs"]["requirement_agent_llm_notes"]
    )


def test_observer_treats_browser_action_prompt_as_executable_test():
    from app.agents import observer_agent

    result = observer_agent.run(
        {
            "user_prompt": (
                "Navigate to http://localhost:4200/. Enter email t@t.com and "
                "password test123. Click login. Validate Dashboard, Profile, "
                "and Logout are present."
            )
        }
    )

    observation = result["observation"]
    assert observation["detected_url"] == "http://localhost:4200/"
    assert observation["task_type"] == "selenium_test_generation"
    assert observation["requires_dom_inspection"] is True
    assert observation["requires_code_generation"] is True
    assert observation["requires_execution"] is True


def test_requirement_fallback_uses_email_field_for_login_prompt():
    from app.agents import requirement_agent

    requirement = requirement_agent._fallback_requirement(
        "Navigate to http://localhost:4200/. Enter email t@t.com and password test123.",
        "http://localhost:4200/",
    )

    assert requirement.steps[1].target_description == "email field"
    assert requirement.steps[1].value_from_env == "APP_USERNAME"
