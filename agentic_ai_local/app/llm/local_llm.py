from __future__ import annotations
import requests
from langchain_ollama import ChatOllama
from app.config import get_settings

class OllamaUnavailableError(RuntimeError):
    pass

def get_chat_model(model: str | None = None) -> ChatOllama:
    settings = get_settings()
    try:
        requests.get(f"{settings.ollama_base_url}/api/tags", timeout=2)
    except Exception as exc:
        raise OllamaUnavailableError("Ollama is not reachable. Start it locally with `ollama serve` and pull a model such as `ollama pull qwen2.5-coder:7b`.") from exc
    return ChatOllama(model=model or settings.local_llm_model, base_url=settings.ollama_base_url, temperature=settings.local_llm_temperature, num_ctx=settings.local_llm_num_ctx)
