from __future__ import annotations
import re
from datetime import datetime, timezone
from pathlib import Path
from app.config import GENERATED_TESTS_DIR, RUN_LOGS_DIR, ROOT_DIR

def timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.lower()).strip("_")
    return slug[:80] or "generated_test"

def relative_to_root(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT_DIR.resolve()))
