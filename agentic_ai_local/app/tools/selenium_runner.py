from __future__ import annotations
import subprocess, sys, time
from pathlib import Path
from app.config import GENERATED_TESTS_DIR, RUN_LOGS_DIR
from app.tools.safety_tool import validate_command
from app.utils.paths import timestamp, relative_to_root

def run_generated_script(file_path: str) -> dict:
    path = (GENERATED_TESTS_DIR.parent / file_path).resolve()
    if not path.is_relative_to(GENERATED_TESTS_DIR.resolve()):
        raise ValueError("Refusing to execute file outside generated_tests/")
    cmd = [sys.executable, str(path)]
    if not validate_command(cmd):
        raise ValueError("Unsafe command rejected")
    start = time.time(); proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    log = RUN_LOGS_DIR / f"execution_{timestamp()}.log"
    log.write_text(f"CMD: {' '.join(cmd)}\nEXIT: {proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}\n")
    return {"success": proc.returncode == 0, "exit_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr, "log_file": relative_to_root(log), "screenshots": [], "duration_seconds": round(time.time()-start, 2), "error_type": None if proc.returncode == 0 else "execution_failed"}
