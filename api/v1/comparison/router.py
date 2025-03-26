from fastapi import APIRouter, Depends, UploadFile, File, Form
from typing import Optional
from sqlalchemy.orm import Session
from db.database import get_db
from domain import ProcessedDataDomain
from schema import ProcessedDataResponse

class ProcessedDataRouter:
    def __init__(self) -> None:
        self.__domain = ProcessedDataDomain()
        
    @property
    def router(self):
        """
        Get the API router for processed data.

        Returns:
            APIRouter: The API router.
        """
        api_router = APIRouter(prefix="/processed_data", tags=["Processed Data"], responses={404: {"description": "Not found"}})
        
        @api_router.post("/upload", response_model=ProcessedDataResponse)
        async def upload_data(
            input_text: str = Form(...),
            image_1: UploadFile = File(...),
            image_2: UploadFile = File(...),
            db: Session = Depends(get_db)
        ):
            """
            Upload two images and text, store in S3 and DB, then process with AI.
            """
            return await self.__domain.process_and_store_data(input_text, image_1, image_2, db)
            
        return api_router
