from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    sql: str = Field(min_length=1, max_length=10000)
    params: dict = Field(default_factory=dict)


class QueryResponse(BaseModel):
    data: list[dict]
    row_count: int
    cached: bool = False
