from abc import ABC, abstractmethod


class BaseLoader(ABC):
    @abstractmethod
    def read(self, relative_path: str) -> str:
        """Return file content as string. Raises FileNotFoundError if missing."""

    @abstractmethod
    def list(self, relative_dir: str) -> list[str]:
        """Return list of relative file paths under relative_dir."""

    def get_config(self) -> "GovernanceConfig":  # type: ignore[name-defined]
        from src.models.config import GovernanceConfig
        import yaml
        try:
            content = self.read("governance.yml")
            return GovernanceConfig.model_validate(yaml.safe_load(content))
        except FileNotFoundError:
            return GovernanceConfig()
