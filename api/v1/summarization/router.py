from fastapi import APIRouter, Depends, status
from .domain import SummarizationDomain
from sqlalchemy.orm import Session
from core.deps import get_db
from .schema import SummarizationCreate, SummarizationResponse

class SummarizationRouter:
    def __init__(self) -> None:
        self.__domain = SummarizationDomain()

    @property
    def router(self):
        """
        Get the API router for text processing.

        Returns:
            APIRouter: The API router.
        """
        api_router = APIRouter(prefix="/text", tags=["text"])

        @api_router.post("/", status_code=status.HTTP_201_CREATED, response_model=SummarizationResponse)
        def create_text_entry(text_data: SummarizationCreate, db: Session = Depends(get_db)):
            """
            API to receive text, store it, process it with AI, and return the result.

            Args:
                text_data (TextCreate): Input text data.
                db (Session): Database session.

            Returns:
                TextResponse: The stored and AI-processed text.
            """
            return self.__domain.create_text_entry(db, text_data)

        @api_router.get("/{text_id}", response_model=SummarizationResponse)
        def get_text_entry(text_id: int, db: Session = Depends(get_db)):
            """
            API to retrieve the processed text by ID.

            Args:
                text_id (int): ID of the text entry.
                db (Session): Database session.

            Returns:
                TextResponse: The stored text with AI results.
            """
            return self.__domain.get_text_entry_by_id(text_id, db)

        return api_router
