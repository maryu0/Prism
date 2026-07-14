from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    model_config = {"populate_by_name": True}

    id: str
    repository_id: str = Field(alias="repositoryId")
    file_path: str = Field(alias="filePath")
    name: str
    type: str
    start_line: int = Field(alias="startLine")
    end_line: int = Field(alias="endLine")
    similarity: float
