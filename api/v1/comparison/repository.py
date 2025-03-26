from datetime import datetime
from typing import Optional
import boto3
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from .model import ProcessedData
import os
class DataRepository:
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
            region_name=os.getenv("AWS_REGION"),
        )
    
    def upload_to_s3(self, file: UploadFile) -> str:
        """Uploads an image to S3 and returns the file URL."""
        try:
            file_extension = file.filename.split(".")[-1]
            file_key = f"uploads/{uuid.uuid4()}.{file_extension}"
            
            self.s3_client.upload_fileobj(file.file, S3_BUCKET_NAME, file_key, ExtraArgs={"ACL": "public-read"})
            
            return f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{file_key}"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"S3 Upload Failed: {str(e)}")
    
    def save_text_to_db(self, db: Session, input_text: str, image_url_1: str, image_url_2: str) -> ProcessedData:
        """Stores input text and image URLs in the database."""
        db_entry = ProcessedData(
            input_text=input_text,
            image_url_1=image_url_1,
            image_url_2=image_url_2,
            created_at=datetime.utcnow()
        )
        db.add(db_entry)
        db.commit()
        db.refresh(db_entry)
        return db_entry
    
    def process_ai_function(self, input_text: str, image_url_1: str, image_url_2: str) -> str:
        """Mock AI processing function - replace with actual logic."""
        processed_result = f"Processed data for text: {input_text} with images {image_url_1} and {image_url_2}"
        return processed_result
    
    def store_processed_data(self, db: Session, data_id: int, processed_text: str) -> ProcessedData:
        """Updates the database entry with AI-processed text."""
        db_entry = db.query(ProcessedData).filter(ProcessedData.id == data_id).first()
        if not db_entry:
            raise HTTPException(status_code=404, detail="Data not found")
        
        db_entry.processed_text = processed_text
        db_entry.processed_at = datetime.utcnow()
        db.commit()
        db.refresh(db_entry)
        return db_entry
