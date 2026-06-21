"""Configuration for the local agent framework."""
from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
GENERATED_TESTS_DIR = ROOT_DIR / "generated_tests"
RUN_LOGS_DIR = ROOT_DIR / "run_logs"
MEMORY_FILE = RUN_LOGS_DIR / "memory.json"

@dataclass(frozen=True)
class Settings:
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    local_llm_model: str = os.getenv("LOCAL_LLM_MODEL", "qwen2.5-coder:7b")
    local_llm_temperature: float = float(os.getenv("LOCAL_LLM_TEMPERATURE", "0.1"))
    local_llm_num_ctx: int = int(os.getenv("LOCAL_LLM_NUM_CTX", "8192"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "2"))
    max_iterations: int = int(os.getenv("MAX_ITERATIONS", "8"))
    headless: bool = os.getenv("HEADLESS", "true").lower() == "true"


def get_settings() -> Settings:
    GENERATED_TESTS_DIR.mkdir(exist_ok=True)
    RUN_LOGS_DIR.mkdir(exist_ok=True)
    (RUN_LOGS_DIR / "screenshots").mkdir(exist_ok=True)
    return Settings()
