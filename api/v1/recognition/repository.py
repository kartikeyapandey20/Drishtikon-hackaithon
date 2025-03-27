from sqlalchemy.orm import Session
from fastapi import HTTPException
from .model import RecognitionData
from .schema import RecognitionCreate, RecognitionResponse
from utils.file import upload_to_s3
import time
import os
from uuid import uuid4
from io import BytesIO

class RecognitionRepository:
    def __init__(self):
        self.s3_bucket = os.environ.get("AWS_BUCKET_NAME")

    def upload_image_to_s3(self, image_bytes: bytes, filename: str) -> str:
        """
        Uploads an image to AWS S3 and returns the file URL.

        Args:
            image_bytes (bytes): The image file as bytes.
            filename (str): Original filename of the image.

        Returns:
            str: The public S3 URL of the uploaded image.

        Raises:
            HTTPException: If upload fails.
        """
        try:
            file_extension = filename.split(".")[-1]
            unique_filename = f"{uuid4()}.{file_extension}"
            
            # Create a BytesIO object from the bytes
            file_obj = BytesIO(image_bytes)
            
            # Upload using the function from utils/file.py
            s3_url = upload_to_s3(file_obj, unique_filename)
            
            # Check if upload was successful
            if s3_url.startswith("Error"):
                raise HTTPException(status_code=500, detail=s3_url)
                
            return s3_url
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")

    def create_recognition_entry(self, text_data: RecognitionCreate, image_bytes: bytes, filename: str, db: Session) -> RecognitionResponse:
        """
        Stores text in DB, uploads image to S3, processes with AI, and returns the result.

        Args:
            text_data (RecognitionCreate): Input text.
            image_bytes (bytes): Image file as bytes.
            filename (str): Original filename of the image.
            db (Session): Database session.

        Returns:
            RecognitionResponse: Stored text, image URL, and AI-processed result.

        Raises:
            HTTPException: If any operation fails.
        """
        try:
            # First upload the image
            image_url = self.upload_image_to_s3(image_bytes, filename)
            
            # Create database entry
            new_entry = RecognitionData(
                input_text=text_data.input_text,
                image_url=image_url,
                result_text=None
            )

            db.add(new_entry)
            db.commit()
            db.refresh(new_entry)

            # AI Processing
            result_text = self.ai_processing(new_entry.input_text)
            new_entry.result_text = result_text
            db.commit()

            return new_entry
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create recognition entry: {str(e)}")

    def get_recognition_entry_by_id(self, recognition_id: int, db: Session) -> RecognitionResponse:
        """
        Retrieve a recognition entry by ID.

        Args:
            recognition_id (int): The ID of the recognition entry.
            db (Session): Database session.

        Raises:
            HTTPException: If not found.

        Returns:
            RecognitionResponse: The recognition entry.
        """
        entry = db.query(RecognitionData).filter(RecognitionData.id == recognition_id).first()

        if not entry:
            raise HTTPException(status_code=404, detail="Recognition entry not found")

        return entry

    def ai_processing(self, text: str) -> str:
        """
        Simulated AI processing function.

        Args:
            text (str): The input text.

        Returns:
            str: AI-processed output.
        """
        time.sleep(2)  # Simulate AI processing delay
        return text.upper()  # Example AI transformation
