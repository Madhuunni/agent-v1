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
