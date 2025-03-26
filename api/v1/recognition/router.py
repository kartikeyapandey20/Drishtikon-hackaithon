from fastapi import APIRouter, Depends, UploadFile, File, status, Query
from sqlalchemy.orm import Session
from core.deps import get_db
from .domain import RecognitionDomain
from .schema import RecognitionCreate, RecognitionResponse

class RecognitionRouter:
    def __init__(self) -> None:
        self.__domain = RecognitionDomain()

    @property
    def router(self):
        """
        Get the API router for recognition processing.

        Returns:
            APIRouter: The API router.
        """
        api_router = APIRouter(prefix="/recognition", tags=["recognition"])

        @api_router.post("/", status_code=status.HTTP_201_CREATED, response_model=RecognitionResponse)
        async def create_recognition_entry(
                input_text: str = Query(..., description="Input text for recognition"),  # Query parameter
                file: UploadFile = File(...),
            db: Session = Depends(get_db)
        ):
            """
            API to receive text & image, store text in DB, upload image to S3, process with AI, and return the result.

            Args:
                text_data (RecognitionCreate): Input text data.
                file (UploadFile): Image file.
                db (Session): Database session.

            Returns:
                RecognitionResponse: The stored text, image URL, and AI-processed result.
            """ 
            image_bytes = await file.read()  # Read the file as bytes
            image_filename = file.filename   # Get the image filename
            
            return self.__domain.create_recognition_entry(db, input_text, image_bytes, image_filename)
        @api_router.get("/{recognition_id}", response_model=RecognitionResponse)
        def get_recognition_entry(recognition_id: int, db: Session = Depends(get_db)):
            """
            API to retrieve processed recognition entry by ID.

            Args:
                recognition_id (int): ID of the recognition entry.
                db (Session): Database session.

            Returns:
                RecognitionResponse: The stored text, image URL, and AI results.
            """
            return self.__domain.get_recognition_entry_by_id(recognition_id, db)

        return api_router
