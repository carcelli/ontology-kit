from pydantic import BaseModel, Field

from agents import Agent


class ClassSpec(BaseModel):
    name: str
    parent: str | None = None  # e.g., "Thing" or an existing class


class PropertySpec(BaseModel):
    name: str
    kind: str  # "object" or "data" (object -> ObjectProperty, data -> DatatypeProperty)
    domain: str  # class name
    range: str  # class name (object) or xsd type hint ("string","float","date")


class SchemaProposal(BaseModel):
    classes: list[ClassSpec] = Field(default_factory=list)
    properties: list[PropertySpec] = Field(default_factory=list)
    rationale: str = "N/A"


SCHEMA_PROMPT = (
    "You are an ontology designer. Propose minimal schema changes for the user's dataset.\n"
    "Return only JSON matching the SchemaProposal schema. Use compact, stable names.\n"
    "Prefer data properties with explicit xsd ranges. Avoid breaking existing names."
)

schema_agent = Agent(
    name="OntologyDesigner",
    instructions=SCHEMA_PROMPT,
    model="gpt-4.1",  # Using standard model following OpenAI examples
    output_type=SchemaProposal,
)
