from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, UploadFile
from core.deps import get_db
from .model import RecognitionData
from .schema import RecognitionCreate, RecognitionResponse
import time
import boto3
import os
from uuid import uuid4

class RecognitionRepository:
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
            region_name=os.getenv("AWS_REGION"),
        )
        self.s3_bucket = os.getenv("AWS_BUCKET_NAME")

    def upload_image_to_s3(self, file: UploadFile) -> str:
        """
        Uploads an image to AWS S3 and returns the file URL.

        Args:
            file (UploadFile): The image file.

        Returns:
            str: The public S3 URL of the uploaded image.
        """
        file_extension = file.filename.split(".")[-1]
        unique_filename = f"{uuid4()}.{file_extension}"

        try:
            self.s3_client.upload_fileobj(
                file.file,
                self.s3_bucket,
                unique_filename,
                ExtraArgs={"ACL": "public-read", "ContentType": file.content_type},
            )
            return f"https://{self.s3_bucket}.s3.amazonaws.com/{unique_filename}"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")

    def create_recognition_entry(self, text_data: RecognitionCreate, file: UploadFile, db: Session = Depends(get_db)) -> RecognitionResponse:
        """
        Stores text in DB, uploads image to S3, processes with AI, and returns the result.

        Args:
            text_data (RecognitionCreate): Input text.
            file (UploadFile): Image file.
            db (Session): Database session.

        Returns:
            RecognitionResponse: Stored text, image URL, and AI-processed result.
        """
        image_url = self.upload_image_to_s3(file)
        new_entry = RecognitionData(input_text=text_data.input_text, image_url=image_url, result_text=None)

        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)

        # AI Processing
        result_text = self.ai_processing(new_entry.input_text)
        new_entry.result_text = result_text
        db.commit()

        return new_entry

    def get_recognition_entry_by_id(self, recognition_id: int, db: Session = Depends(get_db)) -> RecognitionResponse:
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
