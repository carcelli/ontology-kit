from agents import Agent
from pydantic import BaseModel


class MappingItem(BaseModel):
    column: str
    property_iri: str
    notes: str | None = None


class MappingPlan(BaseModel):
    items: list[MappingItem]


MAPPER_PROMPT = (
    "You are a data mapper. Given: (1) a CSV header/sample and (2) the ontology terms, "
    "propose column→property mappings. Prefer existing IRIs. Return only JSON."
)

mapper_agent = Agent(
    name="MapperAgent",
    instructions=MAPPER_PROMPT,
    model="gpt-4.1",
    output_type=MappingPlan,
)
