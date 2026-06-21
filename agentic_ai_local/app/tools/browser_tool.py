from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

import requests
from selenium import webdriver
from selenium.common.exceptions import SessionNotCreatedException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from app.config import RUN_LOGS_DIR, get_settings
from app.tools.dom_extractor import summarize_html
from app.utils.paths import timestamp


def _chrome_browser_version() -> str | None:
    for command in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        try:
            output = subprocess.check_output([command, "--version"], text=True, stderr=subprocess.STDOUT).strip()
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
        match = re.search(r"(\d+(?:\.\d+){0,3})", output)
        if match:
            return match.group(1)
    return None


def _chromedriver_service() -> Service:
    browser_version = _chrome_browser_version()
    if browser_version:
        return Service(ChromeDriverManager(driver_version=browser_version).install())
    return Service(ChromeDriverManager().install())


def _chrome_options(profile_dir: str, *, legacy_headless: bool = False) -> Options:
    settings = get_settings()
    options = Options()
    if settings.headless:
        options.add_argument("--headless" if legacy_headless else "--headless=new")
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-pipe")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--window-size=1920,1080")
    options.page_load_strategy = "eager"
    return options


def _create_chrome_driver(profile_dir: str) -> webdriver.Chrome:
    service = _chromedriver_service()
    try:
        return webdriver.Chrome(service=service, options=_chrome_options(profile_dir))
    except (SessionNotCreatedException, WebDriverException) as exc:
        message = str(exc)
        if "DevToolsActivePort" not in message and "session not created" not in message:
            raise
        return webdriver.Chrome(service=service, options=_chrome_options(profile_dir, legacy_headless=True))


def _read_dom_with_chrome(url: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="agent-dom-chrome-profile-") as profile_dir:
        driver = _create_chrome_driver(profile_dir)
        driver.set_page_load_timeout(30)
        try:
            driver.get(url)
            html = driver.page_source
            snapshot = summarize_html(driver.current_url, html)
            screenshot_dir = RUN_LOGS_DIR / "screenshots"
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            screenshot = screenshot_dir / f"dom_{timestamp()}.png"
            driver.save_screenshot(str(screenshot))
            snapshot["browser"] = "chrome"
            snapshot["screenshot"] = str(Path("run_logs") / "screenshots" / screenshot.name)
            return snapshot
        finally:
            driver.quit()


def _read_dom_with_requests(url: str, error: Exception) -> dict:
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        snapshot = summarize_html(url, resp.text)
        snapshot["browser"] = "requests_fallback"
        snapshot["errors"] = [f"Chrome DOM read failed: {error}"]
        return snapshot
    except Exception as exc:
        return {
            "url": url,
            "title": None,
            "forms": [],
            "inputs": [],
            "buttons": [],
            "links": [],
            "page_text_sample": "",
            "browser": "none",
            "errors": [f"Chrome DOM read failed: {error}", f"Requests fallback failed: {exc}"],
        }


def read_dom(url: str) -> dict:
    """Navigate Chrome to the target URL and summarize the rendered DOM."""
    try:
        return _read_dom_with_chrome(url)
    except Exception as exc:
        return _read_dom_with_requests(url, exc)
