from src.loaders.base_loader import BaseLoader


class TeamAwareLoader(BaseLoader):
    """
    Wraps a base loader and merges team-specific governance content from
    teams/<team>/ on top of domain-level content.

    Merge rules (additive only — teams cannot relax domain constraints):
      - constitutions: domain content + team addendum appended
      - features:      domain checks + team checks (via list())
      - adrs:          domain ADRs + team ADRs (via list())
      - governance.yml: always from base — teams have no access
    """

    def __init__(self, base: BaseLoader, team: str) -> None:
        self._base = base
        self._team = team
        self._prefix = f"teams/{team}"

    def read(self, path: str) -> str:
        content = self._base.read(path)

        # Append team addendum for constitutions
        if path == "constitution.md":
            domain = "global"
        elif path.startswith("constitutions/") and path.endswith(".md"):
            domain = path.removeprefix("constitutions/").removesuffix(".md")
        else:
            return content

        addendum_path = f"{self._prefix}/constitutions/{domain}.md"
        try:
            addendum = self._base.read(addendum_path)
            separator = f"\n\n---\n\n## `{self._team}` team addendum\n\n"
            return content + separator + addendum
        except FileNotFoundError:
            return content

    def list(self, relative_dir: str) -> list[str]:
        base_paths = self._base.list(relative_dir)

        # Add team feature files — team checks extend domain checks
        if relative_dir == "features" or relative_dir.startswith("features/"):
            team_dir = f"{self._prefix}/{relative_dir}"
            try:
                team_paths = self._base.list(team_dir)
                base_paths = base_paths + team_paths
            except (FileNotFoundError, Exception):
                pass

        # Add team ADR files
        if relative_dir in ("adrs", "adrs/global"):
            team_adr_dir = f"{self._prefix}/adrs"
            try:
                team_paths = self._base.list(team_adr_dir)
                base_paths = base_paths + team_paths
            except (FileNotFoundError, Exception):
                pass

        return base_paths

    def get_config(self):
        # Teams never override governance.yml — always use domain config
        return self._base.get_config()
