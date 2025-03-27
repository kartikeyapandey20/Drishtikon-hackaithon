from sqlalchemy.orm import Session
from .repository import RecognitionRepository
from .schema import RecognitionCreate
import time

class RecognitionDomain:
    def __init__(self) -> None:
        self.__repository = RecognitionRepository()

    def create_recognition_entry(self, db: Session, input_text: str, image_bytes: bytes, image_filename: str):
        """
        Creates a new recognition entry with image upload and AI processing.

        Args:
            db (Session): SQLAlchemy session.
            input_text (str): Input text for recognition.
            image_bytes (bytes): Image file as bytes.
            image_filename (str): Original filename of the image.

        Returns:
            dict: Created entry data.
        """
        # Create the recognition data object
        text_data = RecognitionCreate(input_text=input_text)
        
        # Create entry with image upload and AI processing
        entry = self.__repository.create_recognition_entry(
            text_data=text_data,
            image_bytes=image_bytes,
            filename=image_filename,
            db=db
        )
        
        return entry

    def ai_processing(self, text: str) -> str:
        """
        Mock AI function that processes the input text.

        Args:
            text (str): Input text.

        Returns:
            str: AI-processed text.
        """
        time.sleep(2)  # Simulating AI processing time
        return text.upper()  # Example: Convert to uppercase

    def get_recognition_entry_by_id(self, db: Session, entry_id: int):
        """
        Retrieve recognition entry by ID.

        Args:
            db (Session): SQLAlchemy session.
            entry_id (int): Entry ID.

        Returns:
            dict: Recognition entry.
        """
        return self.__repository.get_recognition_entry_by_id(entry_id, db)
