from src.loaders.base_loader import BaseLoader

_KNOWLEDGE_DIR = "knowledge"


def list_knowledge_topics(loader: BaseLoader) -> list[str]:
    topics = []
    for path in loader.list(_KNOWLEDGE_DIR):
        if path.endswith(".md"):
            name = path.split("/")[-1].removesuffix(".md")
            topics.append(name)
    return sorted(topics)


def get_knowledge(loader: BaseLoader, topic: str) -> str:
    path = f"{_KNOWLEDGE_DIR}/{topic}.md"
    return loader.read(path)
