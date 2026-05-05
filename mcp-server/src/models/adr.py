from pydantic import BaseModel


class ADRSummary(BaseModel):
    id: str           # e.g. "001"
    title: str
    status: str       # Accepted | DRAFT | Superseded | Deprecated
    domain: str       # Kafka | Camel | SpringBoot | Helm | Platform
    source_path: str


class ADRContent(ADRSummary):
    content: str
    version: str
