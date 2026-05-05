from pydantic import BaseModel
from typing import Literal

ConstitutionDomain = Literal["global", "kafka", "camel", "springboot", "helm"]


class ConstitutionContent(BaseModel):
    domain: ConstitutionDomain
    content: str
    version: str
    source_path: str
