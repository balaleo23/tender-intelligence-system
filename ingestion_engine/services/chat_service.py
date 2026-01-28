import requests

class OllamaGenerateService:
    def __init__(self, model="llama3"):
        self.url = "http://localhost:11434/api/generate"
        self.model = model

    def ask(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        response = requests.post(self.url, json=payload, timeout=300)
        response.raise_for_status()

        return response.json()["response"]


class OllamaChatService:
    """
    Local LLM using Ollama (free, no API key).
    """

    def __init__(self, model: str = "llama3"):
        self.model = model
        self.url = "http://localhost:11434/api/chat"

    def ask(self, prompt: str) -> str:
        response = requests.post(
            self.url,
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            },
            timeout=300
        )
        response.raise_for_status()
        print(r"ollamachat is getting generated {response.raise_for_status()}")
        return response.json()["response"]
