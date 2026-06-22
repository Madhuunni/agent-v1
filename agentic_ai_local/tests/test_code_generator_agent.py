from pathlib import Path

from app.agents import code_generator_agent


def test_generated_selenium_script_uses_resilient_chrome_options(monkeypatch, tmp_path):
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
    assert "def build_chrome_options(profile_dir: str, *, legacy_headless: bool = False) -> Options:" in source
    assert "--user-data-dir={profile_dir}" in source
    assert "--no-sandbox" in source
    assert "--disable-dev-shm-usage" in source
    assert "--remote-debugging-pipe" in source
    assert "--disable-software-rasterizer" in source
    assert "--no-first-run" in source
    assert "def create_chrome_driver(profile_dir: str) -> webdriver.Chrome:" in source
    assert "legacy_headless=True" in source
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


def test_generated_selenium_script_pins_chromedriver_to_detected_browser(monkeypatch, tmp_path):
    generated_dir = tmp_path / "generated_tests"
    generated_dir.mkdir()
    monkeypatch.setattr(code_generator_agent, "GENERATED_TESTS_DIR", generated_dir)
    monkeypatch.setattr(
        code_generator_agent,
        "relative_to_root",
        lambda path: str(Path(path).relative_to(tmp_path)),
    )

    result = code_generator_agent.run({"test_plan": {"name": "driver pinning", "steps": []}})

    generated_path = tmp_path / result["generated_code"]["file_path"]
    source = generated_path.read_text()

    assert "import re" in source
    assert "import subprocess" in source
    assert "def chrome_browser_version() -> str | None:" in source
    assert "google-chrome" in source
    assert "ChromeDriverManager(driver_version=browser_version).install()" in source
    assert "service = chromedriver_service()" in source
    compile(source, str(generated_path), "exec")


def test_generated_selenium_script_drops_invalid_navigation_and_uses_base_url(monkeypatch, tmp_path):
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
                "name": "invalid navigation login test",
                "base_url": "http://localhost:4200",
                "steps": [
                    {
                        "action": "navigate",
                        "target": "//body",
                        "description": "Invalid locator mistaken for URL",
                    },
                    {
                        "action": "assert_text",
                        "by": "body",
                        "target": "Dashboard",
                        "description": "Verify dashboard",
                    },
                ],
            }
        }
    )

    generated_path = tmp_path / result["generated_code"]["file_path"]
    source = generated_path.read_text()

    assert "driver.get('//body')" not in source
    assert "driver.get('http://localhost:4200')" in source
    compile(source, str(generated_path), "exec")
