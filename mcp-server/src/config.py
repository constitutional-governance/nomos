from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    governance_mode: str = "local"  # "local" | "github"
    governance_repo_path: Path = Path(__file__).parent.parent.parent  # default: repo root
    governance_repo_url: str = ""   # github mode: https://github.com/your-org/govern-mcp
    github_token: str = ""          # github mode
    github_branch: str = "main"
    cache_ttl_seconds: int = 300    # github mode cache TTL
    auth_enabled: bool = False      # set True when OAuth 2.1 is configured
    oauth_endpoint: str = ""
    mcp_server_host: str = "127.0.0.1"  # use 0.0.0.0 in Docker/production
    mcp_server_port: int = 8080
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
