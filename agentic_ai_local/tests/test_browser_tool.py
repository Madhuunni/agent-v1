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
