from pydantic import BaseModel


class ValidationResult(BaseModel):
    valid: bool
    errors: list[str]
    warnings: list[str] = []

    @classmethod
    def ok(cls) -> "ValidationResult":
        return cls(valid=True, errors=[])

    @classmethod
    def fail(cls, *errors: str) -> "ValidationResult":
        return cls(valid=False, errors=list(errors))
