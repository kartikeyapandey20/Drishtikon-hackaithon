from sqlalchemy.orm import Session
from .repository import RecognitionRepository
from .schema import RecognitionCreate
from core.aws_s3 import upload_image_to_s3
import time

class RecognitionDomain:
    def __init__(self) -> None:
        self.__repository = RecognitionRepository()

    def create_recognition_entry(self, db: Session, data: RecognitionCreate, image_bytes: bytes, image_filename: str):
        """
        Stores text in DB, uploads image to S3, and processes AI logic.

        Args:
            db (Session): SQLAlchemy session.
            data (RecognitionCreate): Input text data.
            image_bytes (bytes): Image file as bytes.
            image_filename (str): Original filename of the image.

        Returns:
            dict: Created entry data.
        """
        # Upload image to S3
        image_url = upload_image_to_s3(image_bytes, image_filename)

        # Store text and image URL in DB
        entry = self.__repository.create_entry(db, data, image_url)

        # AI Processing (Mock Example)
        result_text = self.ai_processing(entry.input_text)

        # Update DB with AI result
        self.__repository.update_result_text(db, entry.id, result_text)

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
        return self.__repository.get_entry_by_id(db, entry_id)
