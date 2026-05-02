# The Pria Project
# Ollama Adapter — ollama.py
# Connects to a locally running Ollama instance.
# Ollama must be installed and running with a model loaded.
# Download Ollama from ollama.com if not installed.

import urllib.request
import urllib.error
import json

from adapters.base import BaseAdapter

# ─── CONFIGURATION ────────────────────────────────────────────────────────────

DEFAULT_HOST = "http://localhost:11434"
DEFAULT_MODEL = "llama3"
REQUEST_TIMEOUT = 120  # seconds


class OllamaAdapter(BaseAdapter):
    """
    Adapter for Ollama local inference backend.
    Communicates via Ollama's REST API.
    No external dependencies — uses Python standard library only.
    """

    def __init__(self, model: str = DEFAULT_MODEL, host: str = DEFAULT_HOST):
        self._model = model
        self._host = host.rstrip("/")

    def complete(self, prompt: str) -> str:
        """
        Sends a prompt to Ollama and returns the completion as a string.
        Uses the /api/generate endpoint with streaming disabled.
        """
        url = f"{self._host}/api/generate"

        payload = json.dumps({
            "model": self._model,
            "prompt": prompt,
            "stream": False,
        }).encode("utf-8")

        request = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                body = response.read().decode("utf-8")
                data = json.loads(body)
                return data.get("response", "").strip()

        except urllib.error.URLError as e:
            raise ConnectionError(
                f"Could not reach Ollama at {self._host}. "
                f"Is Ollama running? Error: {e}"
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Ollama returned invalid JSON: {e}")

    def is_available(self) -> bool:
        """
        Checks if Ollama is running and reachable.
        Returns True if the API responds, False otherwise.
        """
        try:
            url = f"{self._host}/api/tags"
            request = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status == 200
        except Exception:
            return False

    def get_model_name(self) -> str:
        """
        Returns the configured model name.
        """
        return self._model