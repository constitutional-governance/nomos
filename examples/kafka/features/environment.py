from src.loaders.local_loader import LocalLoader
from src.config import settings


def before_all(context):
    loader = LocalLoader(settings.governance_repo_path)
    context.governance_config = loader.get_config()
