from __future__ import annotations
import ast
from pathlib import Path
from app.tools.safety_tool import validate_generated_code

def validate_python_file(path: Path) -> tuple[bool, list[str], list[str]]:
    errors: list[str] = []; warnings: list[str] = []
    if not path.exists(): return False, ["File does not exist"], warnings
    code = path.read_text()
    try: tree = ast.parse(code)
    except SyntaxError as exc: return False, [f"Syntax error: {exc}"], warnings
    errors.extend(validate_generated_code(code))
    imports = {n.names[0].name.split('.')[0] for n in ast.walk(tree) if isinstance(n, ast.Import)} | {n.module.split('.')[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    for required in ["selenium", "webdriver_manager", "os"]:
        if required not in imports: errors.append(f"Missing import: {required}")
    if not any(isinstance(n, ast.FunctionDef) and n.name == "main" for n in ast.walk(tree)): errors.append("main() function missing")
    if ".quit(" not in code: errors.append("WebDriver quit is missing")
    if "WebDriverWait" not in code: errors.append("Explicit waits are missing")
    return not errors, errors, warnings
