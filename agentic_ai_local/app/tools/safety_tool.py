from __future__ import annotations
from pathlib import Path
from app.config import GENERATED_TESTS_DIR, ROOT_DIR

FORBIDDEN = ["rm -rf", "sudo", "mkfs", "shutdown", "reboot", "openai", "anthropic", "gemini", "groq"]

def validate_command(command: list[str]) -> bool:
    joined = " ".join(command).lower()
    return not any(token in joined for token in FORBIDDEN)

def validate_file_path(path: str) -> bool:
    try:
        p = (ROOT_DIR / path).resolve()
        return p.is_relative_to(GENERATED_TESTS_DIR.resolve())
    except Exception:
        return False

def validate_generated_code(code: str) -> list[str]:
    errors: list[str] = []
    low = code.lower()
    if any(token in low for token in FORBIDDEN):
        errors.append("Generated code contains forbidden command/provider reference")
    if "password" in low and "app_password" not in low:
        errors.append("Possible hardcoded password detected")
    return errors
