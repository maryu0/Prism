from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

PyObjectId = Annotated[str, BeforeValidator(str)]


def utcnow() -> datetime:
    return datetime.now(UTC)


class MongoModel(BaseModel):
    """Base for documents read back from Mongo: accepts `_id`, serializes as `id`."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: PyObjectId | None = Field(default=None, alias="_id")
