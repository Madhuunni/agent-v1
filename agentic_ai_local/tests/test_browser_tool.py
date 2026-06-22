import subprocess

from app.tools import browser_tool


def test_chrome_browser_version_parses_installed_browser(monkeypatch):
    calls = []

    def fake_check_output(command, **kwargs):
        calls.append(command)
        if command[0] == "google-chrome":
            return "Google Chrome 149.0.7827.53"
        raise FileNotFoundError

    monkeypatch.setattr(browser_tool.subprocess, "check_output", fake_check_output)

    assert browser_tool._chrome_browser_version() == "149.0.7827.53"
    assert calls == [["google-chrome", "--version"]]


def test_chrome_browser_version_falls_back_to_next_binary(monkeypatch):
    def fake_check_output(command, **kwargs):
        if command[0] == "google-chrome":
            raise FileNotFoundError
        if command[0] == "google-chrome-stable":
            raise subprocess.CalledProcessError(1, command)
        return "Chromium 149.0.7827.53 built on Debian"

    monkeypatch.setattr(browser_tool.subprocess, "check_output", fake_check_output)

    assert browser_tool._chrome_browser_version() == "149.0.7827.53"


def test_dom_summary_captures_angular_formcontrolname(tmp_path, monkeypatch):
    from app.tools import dom_extractor

    monkeypatch.setattr(dom_extractor, "RUN_LOGS_DIR", tmp_path)
    monkeypatch.setattr(dom_extractor, "relative_to_root", lambda path: str(path))

    summary = dom_extractor.summarize_html(
        "http://localhost:4200/",
        '<input matinput formcontrolname="email" id="mat-input-0" required="">',
    )

    email_input = summary["inputs"][0]
    assert email_input["form_control_name"] == "email"
    assert email_input["css_selector"] == "#mat-input-0"
    assert email_input["xpath"] == "//*[@id='mat-input-0']"
