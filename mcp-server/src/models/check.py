from pydantic import BaseModel

CheckDomain = str


class Check(BaseModel):
    domain: str
    feature_file: str
    title: str
    status: str    # "enforced" | "draft"
    content: str
    source_path: str
