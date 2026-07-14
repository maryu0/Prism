from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    model_config = {"populate_by_name": True}

    question: str = Field(min_length=1, max_length=1000)


class Citation(BaseModel):
    model_config = {"populate_by_name": True}

    name: str
    type: str
    file_path: str = Field(alias="filePath")
    start_line: int = Field(alias="startLine")
    end_line: int = Field(alias="endLine")


class AskResponse(BaseModel):
    model_config = {"populate_by_name": True}

    answer: str
    citations: list[Citation]
