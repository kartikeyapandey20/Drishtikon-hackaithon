from pydantic import BaseModel

class SummarizationCreate(BaseModel):
    input_text: str

class SummarizationResponse(BaseModel):
    id: int
    input_text: str
    result_text: str | None

    class Config:
        from_attributes = True
