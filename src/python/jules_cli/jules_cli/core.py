from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

# Common configuration for immutable models
# Use alias_generator to convert snake_case (Python) to camelCase (JSON/API)
frozen_config = ConfigDict(frozen=True, alias_generator=to_camel, populate_by_name=True)


class JulesContext(BaseModel):
    """Context passed between Click commands."""

    api_key: str | None = None
