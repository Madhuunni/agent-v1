from pathlib import Path

from app.agents import code_generator_agent


def test_generated_selenium_script_uses_stable_chrome_options(monkeypatch, tmp_path):
    generated_dir = tmp_path / "generated_tests"
    generated_dir.mkdir()
    monkeypatch.setattr(code_generator_agent, "GENERATED_TESTS_DIR", generated_dir)
    monkeypatch.setattr(
        code_generator_agent,
        "relative_to_root",
        lambda path: str(Path(path).relative_to(tmp_path)),
    )

    result = code_generator_agent.run(
        {
            "test_plan": {
                "name": "login test",
                "steps": [
                    {
                        "action": "navigate",
                        "target": "http://localhost:4200",
                        "description": "Open app",
                    }
                ],
            }
        }
    )

    generated_path = tmp_path / result["generated_code"]["file_path"]
    source = generated_path.read_text()

    assert "import tempfile" in source
    assert "def build_chrome_options(profile_dir: str) -> Options:" in source
    assert "--user-data-dir={profile_dir}" in source
    assert "--no-sandbox" in source
    assert "--disable-dev-shm-usage" in source
    assert "--remote-debugging-port=0" in source
    compile(source, str(generated_path), "exec")


def test_generated_selenium_script_adds_base_url_navigation_when_step_missing(monkeypatch, tmp_path):
    generated_dir = tmp_path / "generated_tests"
    generated_dir.mkdir()
    monkeypatch.setattr(code_generator_agent, "GENERATED_TESTS_DIR", generated_dir)
    monkeypatch.setattr(
        code_generator_agent,
        "relative_to_root",
        lambda path: str(Path(path).relative_to(tmp_path)),
    )

    result = code_generator_agent.run(
        {
            "test_plan": {
                "name": "base url login test",
                "base_url": "http://localhost:4200",
                "steps": [
                    {
                        "action": "assert_text",
                        "by": "body",
                        "target": "Dashboard",
                        "description": "Verify dashboard",
                    }
                ],
            }
        }
    )

    generated_path = tmp_path / result["generated_code"]["file_path"]
    source = generated_path.read_text()

    assert 'driver.get(\'http://localhost:4200\')' in source
    assert "driver.set_page_load_timeout(30)" in source
    assert "options.page_load_strategy = \"eager\"" in source
    assert "wait.until(lambda d: d.current_url.startswith('http://localhost:4200'))" in source
    compile(source, str(generated_path), "exec")
