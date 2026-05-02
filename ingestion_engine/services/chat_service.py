import requests

from ingestion_engine.config import settings
from ingestion_engine.utils.logger import get_logger

logger = get_logger(__name__)


class OllamaGenerateService:

    def __init__(self, model: str = None):
        self.model = model or settings.ollama_model
        self.url = f"{settings.ollama_base_url}/api/generate"

    def ask(self, prompt: str) -> str:
        response = requests.post(
            self.url,
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=300,
        )
        response.raise_for_status()
        return response.json()["response"]


class OllamaChatService:

    def __init__(self, model: str = None):
        self.model = model or settings.ollama_model
        self.url = f"{settings.ollama_base_url}/api/chat"

    def ask(self, prompt: str) -> str:
        response = requests.post(
            self.url,
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
            timeout=300,
        )
        response.raise_for_status()
        logger.info("Ollama response generated")
        return response.json()["message"]["content"]
