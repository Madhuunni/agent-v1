from __future__ import annotations
from typing import Literal
from urllib.parse import urlparse
from pydantic import BaseModel, Field, field_validator


Action = Literal["navigate", "click", "type", "select", "assert_text", "assert_url", "wait", "screenshot"]
By = Literal["id", "name", "css", "xpath", "body"]


class LocatorCandidate(BaseModel):
    by: By
    target: str = Field(min_length=1)


def is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


class TestStep(BaseModel):
    action: Action
    by: By | None = None
    target: str = Field(min_length=1)
    value: str | None = None
    value_from_env: str | None = None
    description: str = Field(min_length=1)
    locator_candidates: list[LocatorCandidate] = Field(default_factory=list)

    @field_validator("target")
    @classmethod
    def validate_target_for_action(cls, value: str, info):
        action = info.data.get("action")
        if action == "navigate" and not is_http_url(value):
            raise ValueError("navigate target must be an absolute http(s) URL")
        return value


class TestPlan(BaseModel):
    name: str = Field(min_length=1)
    base_url: str | None = None
    steps: list[TestStep] = Field(default_factory=list)
    assertions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str | None):
        if value is not None and not is_http_url(value):
            raise ValueError("base_url must be an absolute http(s) URL")
        return value
