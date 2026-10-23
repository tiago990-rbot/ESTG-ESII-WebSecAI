from pydantic import BaseModel


class FindingResponse(BaseModel):
    id: int
    title: str
    severity: str
    category: str
    description: str
    recommendation: str

    model_config = {"from_attributes": True}
