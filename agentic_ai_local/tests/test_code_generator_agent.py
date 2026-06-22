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


def test_generated_selenium_script_falls_back_to_semantic_input_locator(monkeypatch, tmp_path):
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
                "name": "semantic email fallback",
                "base_url": "http://localhost:4200",
                "steps": [
                    {
                        "action": "type",
                        "by": "xpath",
                        "target": "//input[@type='email']",
                        "value": "t@t.com",
                        "description": "the email input field",
                    }
                ],
            }
        }
    )

    generated_path = tmp_path / result["generated_code"]["file_path"]
    source = generated_path.read_text()

    assert "TimeoutException" in source
    assert "def _semantic_input_candidates" in source
    assert "input[formcontrolname*='email' i]" in source
    assert 'type_into_element(driver, wait, By.XPATH, "//input[@type=\'email\']", \'the email input field\', env_value(None) if None else \'t@t.com\')' in source
    compile(source, str(generated_path), "exec")


def test_generated_selenium_script_uses_semantic_click_fallback(monkeypatch, tmp_path):
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
                "name": "semantic click fallback",
                "base_url": "http://localhost:4200",
                "steps": [
                    {
                        "action": "click",
                        "by": "xpath",
                        "target": "//button[normalize-space()='Sign in']",
                        "description": "click sign in button",
                    }
                ],
            }
        }
    )

    generated_path = tmp_path / result["generated_code"]["file_path"]
    source = generated_path.read_text()

    assert "def clickable_element" in source
    assert "def click_element" in source
    assert "button, a, input[type='button'], input[type='submit'], [role='button']" in source
    assert "click_element(driver, wait, By.XPATH, \"//button[normalize-space()='Sign in']\", 'click sign in button')" in source
    compile(source, str(generated_path), "exec")


def test_generated_selenium_script_uses_locator_candidates_before_semantic_fallback(monkeypatch, tmp_path):
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
                "name": "candidate fallback",
                "base_url": "http://localhost:4200",
                "steps": [
                    {
                        "action": "click",
                        "by": "css",
                        "target": "button.primary",
                        "description": "click sign in button",
                        "locator_candidates": [
                            {"by": "xpath", "target": "//button[normalize-space()='Sign in']"},
                            {"by": "css", "target": "[data-testid='signin']"},
                        ],
                    }
                ],
            }
        }
    )

    generated_path = tmp_path / result["generated_code"]["file_path"]
    source = generated_path.read_text()

    assert "def find_with_locator_candidates" in source
    assert "locator_name(by)" in source
    assert (
        "click_element(driver, wait, By.CSS_SELECTOR, 'button.primary', 'click sign in button', "
        "[{'by': 'xpath', 'target': \"//button[normalize-space()='Sign in']\"}, {'by': 'css', 'target': \"[data-testid='signin']\"}])"
        in source
    )
    compile(source, str(generated_path), "exec")
