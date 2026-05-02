# The Pria Project
# Adapter Base — base.py
# Defines the interface all backend adapters must implement.
# The core system only talks to adapters, never directly to a model backend.

class BaseAdapter:
    """
    All backend adapters inherit from this class and must implement
    every method defined here. If a method is not implemented,
    calling it will raise a clear error rather than failing silently.
    """

    def complete(self, prompt: str) -> str:
        """
        Sends a prompt to the backend and returns the completion as a string.
        This is the primary method called by Demiurge on every interaction.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement complete()")

    def is_available(self) -> bool:
        """
        Returns True if the backend is reachable and a model is loaded.
        Called by Demiurge at startup to verify the backend before proceeding.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement is_available()")

    def get_model_name(self) -> str:
        """
        Returns the name of the currently loaded model.
        Logged to the soul file at session start.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement get_model_name()")