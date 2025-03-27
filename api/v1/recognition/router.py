from fastapi import APIRouter, Depends, UploadFile, File, status, Query, HTTPException
from sqlalchemy.orm import Session
from core.deps import get_db
from .domain import RecognitionDomain
from .schema import RecognitionResponse

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
            input_text: str = Query(..., description="Input text for recognition"),
            file: UploadFile = File(..., description="Image file to process"),
            db: Session = Depends(get_db)
        ):
            """
            Create a new recognition entry with image upload and AI processing.

            Args:
                input_text (str): Input text for recognition.
                file (UploadFile): Image file to process.
                db (Session): Database session.

            Returns:
                RecognitionResponse: The created recognition entry with processed results.
            """
            try:
                # Read the file content
                image_bytes = await file.read()
                
                # Process the recognition entry
                result = self.__domain.create_recognition_entry(
                    db=db,
                    input_text=input_text,
                    image_bytes=image_bytes,
                    image_filename=file.filename
                )
                
                return result
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @api_router.get("/{recognition_id}", response_model=RecognitionResponse)
        def get_recognition_entry(recognition_id: int, db: Session = Depends(get_db)):
            """
            Retrieve a processed recognition entry by ID.

            Args:
                recognition_id (int): ID of the recognition entry.
                db (Session): Database session.

            Returns:
                RecognitionResponse: The stored text, image URL, and AI results.
            """
            return self.__domain.get_recognition_entry_by_id(db, recognition_id)

        return api_router
