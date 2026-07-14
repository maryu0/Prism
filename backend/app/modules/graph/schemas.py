from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    model_config = {"populate_by_name": True}

    id: str
    label: str
    path: str
    language: str
    component_count: int = Field(alias="componentCount")
    avg_complexity: float = Field(alias="avgComplexity")


class GraphEdge(BaseModel):
    model_config = {"populate_by_name": True}

    source: str
    target: str
    type: str


class RepositoryGraphResponse(BaseModel):
    model_config = {"populate_by_name": True}

    repository_id: str = Field(alias="repositoryId")
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    truncated: bool


class FileComponent(BaseModel):
    model_config = {"populate_by_name": True}

    name: str
    type: str
    start_line: int = Field(alias="startLine")
    end_line: int = Field(alias="endLine")
    complexity_score: int = Field(alias="complexityScore")


class FileComponentsResponse(BaseModel):
    model_config = {"populate_by_name": True}

    file_id: str = Field(alias="fileId")
    components: list[FileComponent]
