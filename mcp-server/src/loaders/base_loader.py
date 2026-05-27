from abc import ABC, abstractmethod


class BaseLoader(ABC):
    @abstractmethod
    def read(self, relative_path: str) -> str:
        """Return file content as string. Raises FileNotFoundError if missing."""

    @abstractmethod
    def list(self, relative_dir: str) -> list[str]:
        """Return list of relative file paths under relative_dir."""

    def validate(self) -> None:
        """Assert the repo is accessible.  Raise FileNotFoundError (or another
        exception) when it is not.  Called by the server before get_config() so
        that NOMOS_ON_UNAVAILABLE can intercept the error before the silent
        FileNotFoundError → GovernanceConfig() fallback in get_config().

        Subclasses override this for loader-specific reachability checks.
        The default implementation is a no-op (GitHub mode surfaces errors
        naturally when the first API call is made).
        """

    def get_config(self) -> "GovernanceConfig":  # type: ignore[name-defined]
        from src.models.config import GovernanceConfig
        import yaml
        try:
            content = self.read("governance.yml")
            return GovernanceConfig.model_validate(yaml.safe_load(content))
        except FileNotFoundError:
            return GovernanceConfig()
