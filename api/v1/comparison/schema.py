from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ProcessedDataRequest(BaseModel):
    input_text: str

class ProcessedDataResponse(BaseModel):
    id: int
    input_text: str
    image_url_1: str
    image_url_2: str
    processed_text: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        orm_mode = True