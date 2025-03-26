from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from core.deps import get_db
from .model import TextData
from .schema import SummarizationCreate, SummarizationResponse
import time

class SummarizationRepository:
    def create_text(self, text_data: SummarizationCreate, db: Session = Depends(get_db)) -> SummarizationResponse:
        """
        Create a new text entry, store it in the database, process it with AI, and update the result.

        Args:
            text_data (TextCreate): Input text from the user.
            db (Session): Database session.

        Returns:
            TextResponse: The stored text entry with AI-processed results.
        """
        new_text = TextData(input_text=text_data.input_text, result_text=None)
        db.add(new_text)
        db.commit()
        db.refresh(new_text)

        # AI Processing
        result_text = "POST"
        new_text.result_text = result_text
        db.commit()

        return new_text

    def get_text_by_id(self, text_id: int, db: Session = Depends(get_db)) -> SummarizationResponse:
        """
        Retrieve a text entry by its ID.

        Args:
            text_id (int): The ID of the text entry.
            db (Session): Database session.

        Raises:
            HTTPException: If text is not found.

        Returns:
            TextResponse: The text entry with AI-processed results.
        """
        text_entry = db.query(TextData).filter(TextData.id == text_id).first()

        if not text_entry:
            raise HTTPException(status_code=404, detail="Text not found")

        return text_entry

    def ai_processing(self, text: str) -> str:
        """
        Simulated AI processing function.

        Args:
            text (str): The input text.

        Returns:
            str: The AI-processed output.
        """
        time.sleep(2)  # Simulate processing delay
        return text.upper()  # Example AI transformation
