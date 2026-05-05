from pydantic import BaseModel
from typing import Literal

CheckDomain = Literal["kafka", "camel", "springboot", "helm"]


class Check(BaseModel):
    domain: CheckDomain
    feature_file: str
    title: str
    status: str    # "enforced" | "draft"
    content: str
    source_path: str
