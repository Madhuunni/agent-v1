from __future__ import annotations
from app.config import GENERATED_TESTS_DIR
from app.schemas.generated_code import GeneratedCode
from app.schemas.test_plan import TestStep
from app.utils.paths import slugify, relative_to_root

def _selector(by: str | None) -> str:
    return {'id':'By.ID','name':'By.NAME','css':'By.CSS_SELECTOR','xpath':'By.XPATH','body':'By.TAG_NAME'}.get(by or 'css','By.CSS_SELECTOR')

def _steps_with_navigation(plan: dict) -> list[dict]:
    steps = list(plan.get('steps') or [])
    has_navigation = any(step.get('action') == 'navigate' and step.get('target') for step in steps)
    base_url = plan.get('base_url')
    if base_url and not has_navigation:
        nav_step = TestStep(action='navigate', target=base_url, description='Navigate to application').model_dump()
        steps.insert(0, nav_step)
    return steps

def run(state: dict) -> dict:
    plan = state.get('test_plan') or {"name":"existing_or_debug_test","steps":[]}
    lines = [
        'from __future__ import annotations',
        'import os',
        'import tempfile',
        'from pathlib import Path',
        'from selenium import webdriver',
        'from selenium.common.exceptions import SessionNotCreatedException, WebDriverException',
        'from selenium.webdriver.chrome.service import Service',
        'from selenium.webdriver.chrome.options import Options',
        'from selenium.webdriver.common.by import By',
        'from selenium.webdriver.support.ui import WebDriverWait',
        'from selenium.webdriver.support import expected_conditions as EC',
        'from webdriver_manager.chrome import ChromeDriverManager',
        '',
        'RUN_LOGS = Path(__file__).resolve().parents[1] / "run_logs"',
        'def env_value(name: str) -> str:',
        '    value = os.getenv(name)',
        '    if not value: raise RuntimeError(f"Required environment variable {name} is missing")',
        '    return value',
        '',
        'def build_chrome_options(profile_dir: str, *, legacy_headless: bool = False) -> Options:',
        '    options = Options()',
        '    if os.getenv("HEADLESS", "true").lower() == "true":',
        '        options.add_argument("--headless" if legacy_headless else "--headless=new")',
        '    options.add_argument(f"--user-data-dir={profile_dir}")',
        '    options.add_argument("--no-sandbox")',
        '    options.add_argument("--disable-dev-shm-usage")',
        '    options.add_argument("--disable-gpu")',
        '    options.add_argument("--remote-debugging-pipe")',
        '    options.add_argument("--disable-software-rasterizer")',
        '    options.add_argument("--disable-extensions")',
        '    options.add_argument("--no-first-run")',
        '    options.add_argument("--no-default-browser-check")',
        '    options.add_argument("--window-size=1920,1080")',
        '    options.page_load_strategy = "eager"',
        '    return options',
        '',
        'def create_chrome_driver(profile_dir: str) -> webdriver.Chrome:',
        '    service = Service(ChromeDriverManager().install())',
        '    try:',
        '        return webdriver.Chrome(service=service, options=build_chrome_options(profile_dir))',
        '    except (SessionNotCreatedException, WebDriverException) as exc:',
        '        message = str(exc)',
        '        if "DevToolsActivePort" not in message and "session not created" not in message:',
        '            raise',
        '        return webdriver.Chrome(service=service, options=build_chrome_options(profile_dir, legacy_headless=True))',
        '',
        'def main() -> None:',
        '    with tempfile.TemporaryDirectory(prefix="selenium-chrome-profile-") as profile_dir:',
        '        driver = create_chrome_driver(profile_dir)',
        '        wait = WebDriverWait(driver, 20)',
        '        driver.set_page_load_timeout(30)',
        '        try:',
    ]
    for step in _steps_with_navigation(plan):
        action=step['action']; target=repr(step['target'])
        lines.append(f"            print({repr(step.get('description','step'))})")
        if action=='navigate':
            lines.append(f"            driver.get({target})")
            lines.append(f"            wait.until(lambda d: d.current_url.startswith({target}))")
        elif action=='type': lines.append(f"            wait.until(EC.visibility_of_element_located(({_selector(step.get('by'))}, {target}))).send_keys(env_value({repr(step.get('value_from_env'))}) if {repr(step.get('value_from_env'))} else {repr(step.get('value') or '')})")
        elif action=='click': lines.append(f"            wait.until(EC.element_to_be_clickable(({_selector(step.get('by'))}, {target}))).click()")
        elif action=='assert_text': lines.append(f"            wait.until(lambda d: {target} in d.find_element(By.TAG_NAME, 'body').text)")
    lines += ['        except Exception:','            RUN_LOGS.mkdir(exist_ok=True)','            screenshot = RUN_LOGS / "screenshots" / "failure.png"','            screenshot.parent.mkdir(exist_ok=True)','            driver.save_screenshot(str(screenshot))','            raise','        finally:','            driver.quit()','','if __name__ == "__main__":','    main()','']
    path = GENERATED_TESTS_DIR / f"{slugify(plan.get('name','generated_test'))}.py"; path.write_text('\n'.join(lines))
    req_env = sorted({s.get('value_from_env') for s in _steps_with_navigation(plan) if s.get('value_from_env')})
    return {"generated_code": GeneratedCode(file_path=relative_to_root(path), summary='Generated Selenium test', requires_env=req_env).model_dump()}
