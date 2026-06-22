from __future__ import annotations
from pydantic import BaseModel, Field
class DomElement(BaseModel):
    tag: str
    type: str | None = None
    name: str | None = None
    id: str | None = None
    placeholder: str | None = None
    form_control_name: str | None = None
    aria_label: str | None = None
    label: str | None = None
    accessible_name: str | None = None
    role: str | None = None
    text: str | None = None
    href: str | None = None
    keywords: list[str] = Field(default_factory=list)
    css_selector: str
    xpath: str
    visible: bool = True
class DomSnapshot(BaseModel):
    url: str
    title: str | None = None
    forms: list[dict] = Field(default_factory=list)
    inputs: list[DomElement] = Field(default_factory=list)
    buttons: list[DomElement] = Field(default_factory=list)
    links: list[dict] = Field(default_factory=list)
    controls: list[DomElement] = Field(default_factory=list)
    page_text_sample: str = ""
    errors: list[str] = Field(default_factory=list)
