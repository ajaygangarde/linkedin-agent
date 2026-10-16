from typing import Optional
from pydantic import BaseModel


class Draft(BaseModel):
    title: str
    subtitle: str
    article: str
    sources: list[str]
    skip_reason: Optional[str] = None


# Written out rather than generated from Draft: OpenAI's strict mode needs every key
# listed in "required" and additionalProperties set to false, which the Pydantic
# default schema does not do for fields that have a default.
DRAFT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "subtitle": {"type": "string"},
        "article": {"type": "string"},
        "sources": {"type": "array", "items": {"type": "string"}},
        "skip_reason": {"type": ["string", "null"]},
    },
    "required": ["title", "subtitle", "article", "sources", "skip_reason"],
    "additionalProperties": False,
}


class Review(BaseModel):
    """One reviewer verdict per criterion, plus the revised article."""
    source_fidelity: str
    original_application: str
    technical_accuracy: str
    storytelling: str
    unsupported_claims: list[str]
    revised_article: str


REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "source_fidelity": {"type": "string"},
        "original_application": {"type": "string"},
        "technical_accuracy": {"type": "string"},
        "storytelling": {"type": "string"},
        "unsupported_claims": {"type": "array", "items": {"type": "string"}},
        "revised_article": {"type": "string"},
    },
    "required": ["source_fidelity", "original_application", "technical_accuracy",
                 "storytelling", "unsupported_claims", "revised_article"],
    "additionalProperties": False,
}
