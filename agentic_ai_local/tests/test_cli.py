from typer.testing import CliRunner

from app import cli as cli_module


runner = CliRunner()


def fake_observation(url: str, *, executable: bool = True) -> dict:
    return {
        "user_goal": "goal",
        "task_type": "selenium_test_generation" if executable else "browser_inspection",
        "detected_url": url,
        "requires_dom_inspection": executable,
        "requires_code_generation": executable,
        "requires_execution": executable,
        "requires_debugging": False,
        "available_agents": [],
        "available_tools": [],
        "known_context": {},
        "existing_generated_tests": [],
        "existing_run_logs": [],
        "risks": [],
    }


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


def test_observer_uses_llm_observation(monkeypatch):
    from app.agents import observer_agent
    from app.schemas.observation import Observation

    monkeypatch.setattr(observer_agent, "invoke_json", lambda schema, system, payload: Observation.model_validate(fake_observation("http://localhost:4200")))

    result = observer_agent.run({"user_prompt": "Generate Selenium test for http://localhost:4200)."})

    assert result["observation"]["detected_url"] == "http://localhost:4200"


def test_requirement_agent_invokes_local_llm(monkeypatch):
    from app.agents import requirement_agent

    calls = []

    class FakeModel:
        def invoke(self, prompt):
            calls.append(prompt)
            return type("Response", (), {"content": "local llm checklist"})()

    monkeypatch.setattr(requirement_agent, "get_chat_model", lambda: FakeModel())
    monkeypatch.setattr(requirement_agent, "invoke_json", lambda schema, system, payload: schema.model_validate({"name":"n","description":"d","base_url":"http://localhost:4200","preconditions":[],"steps":[],"success_criteria":[],"missing_information":[]}))

    result = requirement_agent.run(
        {
            "user_prompt": "Generate and run Selenium login test for http://localhost:4200",
            "observation": {"detected_url": "http://localhost:4200"},
            "agent_outputs": {},
        }
    )

    assert calls
    assert result["agent_outputs"]["requirement_agent_llm_notes"] == "local llm checklist"


def test_observer_treats_browser_action_prompt_as_executable_test(monkeypatch):
    from app.agents import observer_agent
    from app.schemas.observation import Observation

    monkeypatch.setattr(observer_agent, "invoke_json", lambda schema, system, payload: Observation.model_validate(fake_observation("http://localhost:4200/")))

    result = observer_agent.run({"user_prompt": "Navigate to http://localhost:4200/. Enter email t@t.com and password test123. Click login."})

    observation = result["observation"]
    assert observation["detected_url"] == "http://localhost:4200/"
    assert observation["task_type"] == "selenium_test_generation"
    assert observation["requires_dom_inspection"] is True
    assert observation["requires_code_generation"] is True
    assert observation["requires_execution"] is True


def test_agent_activity_logs_to_separate_timestamped_files(tmp_path):
    from app.utils import agent_logging

    agent_logging.configure_agent_file_logging(
        log_dir=tmp_path,
        run_timestamp="20260622_095158",
        verbose=True,
    )

    try:
        agent_logging.log_agent_start("observer_agent", {"user_prompt": "observe"})
        agent_logging.log_agent_end("observer_agent", {"observation": {"task_type": "demo"}})
        agent_logging.log_agent_start("planner_agent", {"user_prompt": "plan"})
        agent_logging.log_llm_request("planner_agent", {"input": "plan"})
        agent_logging.log_agent_end("planner_agent", {"plan": {"agent_sequence": []}})
    finally:
        agent_logging.close_agent_file_logging()

    observer_log = tmp_path / "observer_20260622_095158.log"
    planner_log = tmp_path / "planner_20260622_095158.log"

    assert observer_log.exists()
    assert planner_log.exists()
    assert "[observer_agent] agent call started" in observer_log.read_text()
    assert "[planner_agent] agent call started" in planner_log.read_text()
    assert "LLM request JSON" in planner_log.read_text()
    assert "planner_agent" not in observer_log.read_text()


def test_schema_layer_logs_reuse_agent_timestamped_files(tmp_path):
    from app.utils import agent_logging

    agent_logging.configure_agent_file_logging(
        log_dir=tmp_path,
        run_timestamp="20260622_111220",
        verbose=True,
    )

    try:
        agent_logging.log_agent_start("observer_agent", {"user_prompt": "observe"})
        agent_logging.log_llm_request("Observation", {"input": "observe"})
        agent_logging.log_agent_start("requirement_agent", {"user_prompt": "require"})
        agent_logging.log_llm_request("Requirement", {"input": "require"})
        agent_logging.log_agent_start("locator_agent", {"user_prompt": "locate"})
        agent_logging.log_llm_request("LocatorResult", {"input": "locate"})
        agent_logging.log_agent_start("test_plan_agent", {"user_prompt": "plan"})
        agent_logging.log_llm_request("TestPlan", {"input": "plan"})
    finally:
        agent_logging.close_agent_file_logging()

    assert (tmp_path / "observer_20260622_111220.log").exists()
    assert (tmp_path / "requirement_20260622_111220.log").exists()
    assert (tmp_path / "locator_20260622_111220.log").exists()
    assert (tmp_path / "test_plan_20260622_111220.log").exists()
    assert not (tmp_path / "Observation_20260622_111220.log").exists()
    assert not (tmp_path / "Requirement_20260622_111220.log").exists()
    assert not (tmp_path / "LocatorResult_20260622_111220.log").exists()
    assert not (tmp_path / "TestPlan_20260622_111220.log").exists()

def test_report_agent_suppresses_missing_information_after_successful_execution():
    from app.agents import report_agent

    result = report_agent.run(
        {
            "user_prompt": "Navigate to http://localhost:4200/ and submit login form",
            "observation": {"task_type": "selenium_test_generation"},
            "completed_agents": ["requirement_agent", "executor_agent"],
            "execution_plan": {"agent_sequence": ["requirement_agent", "executor_agent"]},
            "requirement": {
                "missing_information": [
                    "The exact selectors for the email input field, password input field, and submit button are not provided."
                ]
            },
            "execution_result": {"success": True, "log_file": "run_logs/execution.log"},
        }
    )

    assert "## Execution Status" in result["final_report"]
    assert "- Success: True" in result["final_report"]
    assert "## Missing Information" not in result["final_report"]
