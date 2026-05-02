# The Pria Project
# Mock Adapter — mock.py
# A fake backend for testing purposes.
# Returns scripted responses without needing a real model running.
# Use this to test Demiurge and Context Assembly before Ollama is set up.

from adapters.base import BaseAdapter


class MockAdapter(BaseAdapter):
    """
    Simulates a model backend for testing.
    Responses are predictable and controllable.
    No network calls, no model required.
    """

    def __init__(self, model_name: str = "mock-model", responses: list = None):
        """
        model_name  — name reported by get_model_name()
        responses   — optional list of strings to return in sequence.
                      If the list runs out, a default response is returned.
        """
        self._model_name = model_name
        self._responses = responses or []
        self._call_count = 0

    def complete(self, prompt: str) -> str:
        """
        Returns the next scripted response if available.
        Falls back to a default response when the list is exhausted.
        Records how many times it has been called.
        """
        self._call_count += 1

        if self._responses:
            index = min(self._call_count - 1, len(self._responses) - 1)
            return self._responses[index]

        return f"[Mock response {self._call_count}] I have received your prompt and am responding."

    def is_available(self) -> bool:
        """
        Always returns True. The mock backend is always available.
        """
        return True

    def get_model_name(self) -> str:
        """
        Returns the configured mock model name.
        """
        return self._model_name

    def get_call_count(self) -> int:
        """
        Returns how many times complete() has been called.
        Useful for verifying Demiurge called the adapter the expected number of times.
        """
        return self._call_count

    def reset(self):
        """
        Resets call count. Useful between tests.
        """
        self._call_count = 0