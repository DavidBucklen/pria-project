# The Pria Project
# Ollama Adapter — ollama.py
# Connects to a locally running Ollama instance.
# Ollama must be installed and running with a model loaded.
# Download Ollama from ollama.com if not installed.

import urllib.request
import urllib.error
import json
import base64
import os
from adapters.base import BaseAdapter

# ─── CONFIGURATION ────────────────────────────────────────────────────────────

DEFAULT_HOST = "http://localhost:11434"
DEFAULT_MODEL = "llama3"
REQUEST_TIMEOUT = 120  # seconds

# Supported image formats for vision models.
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

# Supported text file formats for context injection.
TEXT_EXTENSIONS = {".txt", ".md", ".py", ".json", ".csv", ".html", ".xml"}


class OllamaAdapter(BaseAdapter):
    """
    Adapter for Ollama local inference backend.
    Communicates via Ollama's REST API.
    Supports text prompts, image attachments, and text file injection.
    No external dependencies beyond standard library — pypdf optional for PDFs.
    """

    def __init__(self, model: str = DEFAULT_MODEL, host: str = DEFAULT_HOST):
        self._model = model
        self._host = host.rstrip("/")

    def complete(self, prompt: str, images: list = None) -> str:
        """
        Sends a prompt to Ollama and returns the completion as a string.
        Uses the /api/generate endpoint with streaming disabled.

        images — optional list of base64-encoded image strings.
                 Only used with vision-capable models like Gemma 4.
        """
        url = f"{self._host}/api/generate"

        payload_dict = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
        }

        # Add images if provided and model supports vision.
        if images:
            payload_dict["images"] = images

        payload = json.dumps(payload_dict).encode("utf-8")

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

    def complete_with_file(self, prompt: str, file_path: str) -> str:
        """
        Sends a prompt with an attached file to Ollama.
        Images are passed via the vision API.
        Text files and PDFs are extracted and injected into the prompt.

        file_path — absolute or relative path to the file.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()

        # ── Image files — pass via vision API ────────────────────────────────
        if ext in IMAGE_EXTENSIONS:
            with open(file_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            return self.complete(prompt, images=[image_data])

        # ── Text files — inject content into prompt ───────────────────────────
        if ext in TEXT_EXTENSIONS:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                file_content = f.read()
            filename = os.path.basename(file_path)
            augmented_prompt = (
                f"{prompt}\n\n"
                f"[Attached file: {filename}]\n"
                f"{file_content}\n"
                f"[End of attached file]"
            )
            return self.complete(augmented_prompt)

        # ── PDF files — extract text and inject ───────────────────────────────
        if ext == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                text = "\n".join(
                    page.extract_text() or "" for page in reader.pages
                )
                filename = os.path.basename(file_path)
                augmented_prompt = (
                    f"{prompt}\n\n"
                    f"[Attached PDF: {filename}]\n"
                    f"{text}\n"
                    f"[End of attached PDF]"
                )
                return self.complete(augmented_prompt)
            except ImportError:
                raise ImportError(
                    "pypdf is required for PDF support. "
                    "Install it with: pip install pypdf --break-system-packages"
                )

        raise ValueError(
            f"Unsupported file type: {ext}. "
            f"Supported: images ({', '.join(IMAGE_EXTENSIONS)}), "
            f"text ({', '.join(TEXT_EXTENSIONS)}), .pdf"
        )

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