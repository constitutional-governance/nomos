from pydantic import BaseModel

ConstitutionDomain = str


class ConstitutionContent(BaseModel):
    domain: str
    content: str
    version: str
    source_path: str
