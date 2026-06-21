from __future__ import annotations
from app.config import GENERATED_TESTS_DIR
from app.schemas.generated_code import GeneratedCode
from app.utils.paths import slugify, relative_to_root

def _selector(by: str | None) -> str:
    return {'id':'By.ID','name':'By.NAME','css':'By.CSS_SELECTOR','xpath':'By.XPATH','body':'By.TAG_NAME'}.get(by or 'css','By.CSS_SELECTOR')

def run(state: dict) -> dict:
    plan = state.get('test_plan') or {"name":"existing_or_debug_test","steps":[]}
    lines = [
        'from __future__ import annotations',
        'import os',
        'import tempfile',
        'from pathlib import Path',
        'from selenium import webdriver',
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
        'def build_chrome_options(profile_dir: str) -> Options:',
        '    options = Options()',
        '    if os.getenv("HEADLESS", "true").lower() == "true":',
        '        options.add_argument("--headless=new")',
        '    options.add_argument(f"--user-data-dir={profile_dir}")',
        '    options.add_argument("--no-sandbox")',
        '    options.add_argument("--disable-dev-shm-usage")',
        '    options.add_argument("--disable-gpu")',
        '    options.add_argument("--remote-debugging-port=0")',
        '    options.add_argument("--window-size=1920,1080")',
        '    return options',
        '',
        'def main() -> None:',
        '    with tempfile.TemporaryDirectory(prefix="selenium-chrome-profile-") as profile_dir:',
        '        options = build_chrome_options(profile_dir)',
        '        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)',
        '        wait = WebDriverWait(driver, 20)',
        '        try:',
    ]
    for step in plan.get('steps', []):
        action=step['action']; target=repr(step['target'])
        lines.append(f"            print({repr(step.get('description','step'))})")
        if action=='navigate': lines.append(f"            driver.get({target})")
        elif action=='type': lines.append(f"            wait.until(EC.visibility_of_element_located(({_selector(step.get('by'))}, {target}))).send_keys(env_value({repr(step.get('value_from_env'))}) if {repr(step.get('value_from_env'))} else {repr(step.get('value') or '')})")
        elif action=='click': lines.append(f"            wait.until(EC.element_to_be_clickable(({_selector(step.get('by'))}, {target}))).click()")
        elif action=='assert_text': lines.append(f"            wait.until(lambda d: {target} in d.find_element(By.TAG_NAME, 'body').text)")
    lines += ['        except Exception:','            RUN_LOGS.mkdir(exist_ok=True)','            screenshot = RUN_LOGS / "screenshots" / "failure.png"','            screenshot.parent.mkdir(exist_ok=True)','            driver.save_screenshot(str(screenshot))','            raise','        finally:','            driver.quit()','','if __name__ == "__main__":','    main()','']
    path = GENERATED_TESTS_DIR / f"{slugify(plan.get('name','generated_test'))}.py"; path.write_text('\n'.join(lines))
    req_env = sorted({s.get('value_from_env') for s in plan.get('steps', []) if s.get('value_from_env')})
    return {"generated_code": GeneratedCode(file_path=relative_to_root(path), summary='Generated Selenium test', requires_env=req_env).model_dump()}
