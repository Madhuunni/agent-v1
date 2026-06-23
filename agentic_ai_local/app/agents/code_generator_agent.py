from __future__ import annotations
from app.config import GENERATED_TESTS_DIR
from app.schemas.generated_code import GeneratedCode
from app.schemas.test_plan import TestStep, is_http_url
from app.utils.paths import slugify, relative_to_root

def _selector(by: str | None) -> str:
    return {'id':'By.ID','name':'By.NAME','css':'By.CSS_SELECTOR','xpath':'By.XPATH','body':'By.TAG_NAME'}.get(by or 'css','By.CSS_SELECTOR')

def _steps_with_navigation(plan: dict) -> list[dict]:
    """Ensure generated Selenium scripts always start with a valid app URL.

    Local LLMs can occasionally confuse Selenium locators with navigation
    targets (for example, ``//body``). Selenium's ``driver.get`` only accepts
    absolute URLs, so invalid navigation steps are discarded and replaced with
    the plan ``base_url`` when it is available.
    """

    steps = list(plan.get('steps') or [])
    base_url = plan.get('base_url')
    valid_steps = [
        step
        for step in steps
        if step.get('action') != 'navigate' or is_http_url(str(step.get('target') or ''))
    ]
    has_navigation = any(step.get('action') == 'navigate' for step in valid_steps)
    if base_url and is_http_url(str(base_url)) and not has_navigation:
        nav_step = TestStep(action='navigate', target=base_url, description='Navigate to application').model_dump()
        valid_steps.insert(0, nav_step)
    return valid_steps

def run(state: dict) -> dict:
    """Render the structured test plan into an executable Selenium script.

    The generated script owns browser startup, ChromeDriver resolution, each
    planned user action/assertion, screenshot capture on failure, and cleanup.
    Metadata returned here tells later agents where the file was written and
    which environment variables are needed to run it.
    """

    plan = state.get('test_plan') or {"name":"existing_or_debug_test","steps":[]}
    lines = [
        'from __future__ import annotations',
        'import os',
        'import re',
        'import subprocess',
        'import tempfile',
        'from pathlib import Path',
        'from selenium import webdriver',
        'from selenium.common.exceptions import SessionNotCreatedException, TimeoutException, WebDriverException',
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
        'def chrome_browser_version() -> str | None:',
        '    for command in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):',
        '        try:',
        '            output = subprocess.check_output([command, "--version"], text=True, stderr=subprocess.STDOUT).strip()',
        '        except (FileNotFoundError, subprocess.CalledProcessError):',
        '            continue',
        '        match = re.search(r"(\\d+(?:\\.\\d+){0,3})", output)',
        '        if match:',
        '            return match.group(1)',
        '    return None',
        '',
        'def chromedriver_service() -> Service:',
        '    browser_version = chrome_browser_version()',
        '    if browser_version:',
        '        return Service(ChromeDriverManager(driver_version=browser_version).install())',
        '    return Service(ChromeDriverManager().install())',
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
        '    service = chromedriver_service()',
        '    try:',
        '        return webdriver.Chrome(service=service, options=build_chrome_options(profile_dir))',
        '    except (SessionNotCreatedException, WebDriverException) as exc:',
        '        message = str(exc)',
        '        if "DevToolsActivePort" not in message and "session not created" not in message:',
        '            raise',
        '        return webdriver.Chrome(service=service, options=build_chrome_options(profile_dir, legacy_headless=True))',
        '',
        '',
        'def locator_name(by) -> str:',
        '    reverse = {By.ID: "id", By.NAME: "name", By.CSS_SELECTOR: "css", By.XPATH: "xpath", By.TAG_NAME: "body"}',
        '    return reverse.get(by, by)',
        '',
        'def get_by(by_name: str):',
        '    mapping = {"id": By.ID, "name": By.NAME, "css": By.CSS_SELECTOR, "xpath": By.XPATH, "body": By.TAG_NAME}',
        '    if by_name not in mapping:',
        '        raise RuntimeError(f"Unsupported locator strategy: {by_name}")',
        '    return mapping[by_name]',
        '',
        'def _locator_matches(driver: webdriver.Chrome, by: str, target: str):',
        '    return driver.find_elements(by, target)',
        '',
        'def find_with_locator_candidates(driver: webdriver.Chrome, wait: WebDriverWait, locators: list[dict], condition: str, description: str):',
        '    errors = []',
        '    for locator in locators:',
        '        try:',
        '            selenium_by = get_by(locator["by"])',
        '            target = locator["target"]',
        '            if condition == "clickable":',
        '                return wait.until(EC.element_to_be_clickable((selenium_by, target)))',
        '            if condition == "present":',
        '                return wait.until(EC.presence_of_element_located((selenium_by, target)))',
        '            return wait.until(EC.visibility_of_element_located((selenium_by, target)))',
        '        except Exception as exc:',
        '            errors.append({"locator": locator, "error": str(exc)})',
        '    raise TimeoutException(f"Unable to find {description} with locator candidates: {errors}")',
        '',
        'FIELD_MATCH_ATTRIBUTES = ("name", "id", "placeholder", "aria-label", "formcontrolname", "autocomplete", "data-testid")',
        'STOP_WORDS = {"the", "a", "an", "to", "and", "or", "field", "input", "enter", "type", "into", "value", "with", "using"}',
        '',
        'def meaningful_words(*parts: str) -> list[str]:',
        '    words = []',
        '    for part in parts:',
        '        for word in re.findall(r"[a-z0-9_-]+", (part or "").lower()):',
        '            if len(word) > 1 and word not in STOP_WORDS and word not in words:',
        '                words.append(word)',
        '    return words',
        '',
        'def css_string(value: str) -> str:',
        '    return "\'" + value.replace("\\\\", "\\\\\\\\").replace("\'", "\\\\\'") + "\'"',
        '',
        'def semantic_input_selectors(description: str, target: str) -> list[str]:',
        '    selectors = []',
        '    for word in meaningful_words(description, target):',
        '        selectors.append(f"input[type={css_string(word)}]")',
        '        selectors.extend(f"input[{attribute}*={css_string(word)} i]" for attribute in FIELD_MATCH_ATTRIBUTES)',
        '        selectors.extend(f"textarea[{attribute}*={css_string(word)} i]" for attribute in FIELD_MATCH_ATTRIBUTES)',
        '        selectors.extend(f"[contenteditable=\\"true\\"][{attribute}*={css_string(word)} i]" for attribute in FIELD_MATCH_ATTRIBUTES)',
        '    return selectors',
        '',
        'def _semantic_input_candidates(driver: webdriver.Chrome, description: str, target: str):',
        '    candidates = []',
        '    selectors = semantic_input_selectors(description, target)',
        '    if selectors:',
        '        candidates.extend(driver.find_elements(By.CSS_SELECTOR, ", ".join(selectors)))',
        '    if not candidates:',
        '        candidates.extend(driver.find_elements(By.CSS_SELECTOR, \'input, textarea, [contenteditable=\\"true\\"]\'))',
        '    seen = set()',
        '    unique = []',
        '    for element in candidates:',
        '        element_id = element.id',
        '        if element_id not in seen and element.is_displayed() and element.is_enabled():',
        '            seen.add(element_id)',
        '            unique.append(element)',
        '    return unique',
        '',
        'def input_element(driver: webdriver.Chrome, by: str, target: str, description: str):',
        '    matches = _locator_matches(driver, get_by(locator_name(by)), target)',
        '    for element in matches:',
        '        if element.is_displayed() and element.is_enabled():',
        '            return element',
        '    semantic_matches = _semantic_input_candidates(driver, description, target)',
        '    if semantic_matches:',
        '        return semantic_matches[0]',
        '    return False',
        '',
        'def clickable_element(driver: webdriver.Chrome, by: str, target: str, description: str):',
        '    matches = _locator_matches(driver, get_by(locator_name(by)), target)',
        '    for element in matches:',
        '        if element.is_displayed() and element.is_enabled():',
        '            return element',
        '    words = [w for w in re.findall(r\"[a-z0-9]+\", description.lower()) if w not in {\"the\", \"a\", \"an\", \"to\", \"and\", \"button\", \"link\", \"click\"}]',
        '    for element in driver.find_elements(By.CSS_SELECTOR, \"button, a, input[type=\'button\'], input[type=\'submit\'], [role=\'button\']\"):',
        '        haystack = \" \".join(filter(None, [element.text, element.get_attribute(\"aria-label\"), element.get_attribute(\"name\"), element.get_attribute(\"id\"), element.get_attribute(\"value\")])).lower()',
        '        if element.is_displayed() and element.is_enabled() and any(word in haystack for word in words):',
        '            return element',
        '    return False',
        '',
        'def click_element(driver: webdriver.Chrome, wait: WebDriverWait, by: str, target: str, description: str, locator_candidates: list[dict] | None = None) -> None:',
        '    try:',
        '        locators = [{"by": locator_name(by), "target": target}, *(locator_candidates or [])]',
        '        element = find_with_locator_candidates(driver, wait, locators, "clickable", description)',
        '    except TimeoutException:',
        '        element = wait.until(lambda d: clickable_element(d, by, target, description))',
        '    driver.execute_script(\"arguments[0].scrollIntoView({block: \\\"center\\\"});\", element)',
        '    element.click()',
        '',
        'def type_into_element(driver: webdriver.Chrome, wait: WebDriverWait, by: str, target: str, description: str, value: str, locator_candidates: list[dict] | None = None) -> None:',
        '    try:',
        '        locators = [{"by": locator_name(by), "target": target}, *(locator_candidates or [])]',
        '        element = find_with_locator_candidates(driver, wait, locators, "visible", description)',
        '    except TimeoutException:',
        '        element = wait.until(lambda d: input_element(d, by, target, description))',
        '    element.clear()',
        '    element.send_keys(value)',
        '',
        'def main() -> None:',
        '    with tempfile.TemporaryDirectory(prefix="selenium-chrome-profile-") as profile_dir:',
        '        driver = create_chrome_driver(profile_dir)',
        '        wait = WebDriverWait(driver, 20)',
        '        driver.set_page_load_timeout(30)',
        '        try:',
    ]
    steps = _steps_with_navigation(plan)
    if not steps:
        lines.append('            pass')
    emitters = {
        'navigate': lambda step, target: [f"            driver.get({target})", f"            wait.until(lambda d: d.current_url.startswith({target}))"],
        'type': lambda step, target: [f"            type_into_element(driver, wait, {_selector(step.get('by'))}, {target}, {repr(step.get('description') or '')}, env_value({repr(step.get('value_from_env'))}) if {repr(step.get('value_from_env'))} else {repr(step.get('value') or '')}{', ' + repr(step.get('locator_candidates')) if step.get('locator_candidates') else ''})"],
        'click': lambda step, target: [f"            click_element(driver, wait, {_selector(step.get('by'))}, {target}, {repr(step.get('description') or '')}{', ' + repr(step.get('locator_candidates')) if step.get('locator_candidates') else ''})"],
        'assert_text': lambda step, target: [f"            wait.until(lambda d: {target} in d.find_element(By.TAG_NAME, 'body').text)"],
    }
    for step in steps:
        target=repr(step['target'])
        lines.append(f"            print({repr(step.get('description','step'))})")
        lines.extend(emitters.get(step['action'], lambda _step, _target: [f"            print('Skipped unsupported action: {step['action']}')"])(step, target))
    lines += ['        except Exception:','            RUN_LOGS.mkdir(exist_ok=True)','            screenshot = RUN_LOGS / "screenshots" / "failure.png"','            screenshot.parent.mkdir(exist_ok=True)','            driver.save_screenshot(str(screenshot))','            raise','        finally:','            driver.quit()','','if __name__ == "__main__":','    main()','']
    path = GENERATED_TESTS_DIR / f"{slugify(plan.get('name','generated_test'))}.py"; path.write_text('\n'.join(lines))
    req_env = sorted({s.get('value_from_env') for s in steps if s.get('value_from_env')})
    return {"generated_code": GeneratedCode(file_path=relative_to_root(path), summary='Generated Selenium test', requires_env=req_env).model_dump()}
