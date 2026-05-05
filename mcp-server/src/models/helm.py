from typing import Literal
from pydantic import BaseModel

HelmServiceType = Literal["kafka_consumer", "kafka_producer", "kafka_processor", "camel_integration"]


class HelmTemplate(BaseModel):
    service_type: HelmServiceType
    description: str
    values_yml: str
    notes: list[str]
