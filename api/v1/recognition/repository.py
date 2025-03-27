from sqlalchemy.orm import Session
from fastapi import HTTPException
from .model import RecognitionData
from .schema import RecognitionCreate, RecognitionResponse
from utils.file import upload_to_s3
import time
import os
from uuid import uuid4
from io import BytesIO
import google.generativeai as genai
import PIL.Image
from dotenv import load_dotenv
import io
load_dotenv()

class RecognitionRepository:
    def __init__(self):
        self.s3_bucket = os.environ.get("AWS_BUCKET_NAME")
        # Configure Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.vision_model = genai.GenerativeModel('gemini-2.0-flash')

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

    def analyze_image(self, image_bytes: bytes, analysis_type: str) -> str:
        """
        Analyze image based on specified type using Gemini Vision.

        Args:
            image_bytes (bytes): The image data
            analysis_type (str): Type of analysis to perform (currency, hazard, color, etc.) or user's specific query

        Returns:
            str: The analysis result
        """
        try:
            # Convert bytes to PIL Image
            image = PIL.Image.open(io.BytesIO(image_bytes))

            # Define prompts based on analysis type
            prompts = {
                "currency": """
                You are a currency recognition expert. Please analyze this image and provide:
                1. The currency denomination
                2. The country of origin
                3. Any security features visible
                4. The condition of the currency
                Please describe this in a clear, accessible way for blind users.
                """,
                "hazard": """
                You are a safety expert. Please analyze this image and identify:
                1. Any potential hazards or safety concerns
                2. The level of risk (low, medium, high)
                3. Recommended safety precautions
                4. Emergency procedures if applicable
                Please describe this in a clear, accessible way for blind users.
                """,
                "color": """
                You are a color analysis expert. Please analyze this image and describe:
                1. The main colors present
                2. Color combinations and patterns
                3. Color intensity and brightness
                4. Any notable color contrasts
                Please describe this in a clear, accessible way for blind users.
                """
            }

            # Get the appropriate prompt or create a custom one based on user's query
            if analysis_type in prompts:
                prompt = prompts[analysis_type]
            else:
                prompt = f"""
                You are a visual analysis expert. The user wants to know about: "{analysis_type}"
                Please analyze this image and provide:
                1. A detailed description focusing on aspects related to the user's query
                2. Important details and context relevant to the query
                3. Any notable features or patterns that might be of interest
                4. Additional relevant information that could help understand the image better
                Please describe this in a clear, accessible way for blind users.
                """

            # Generate response using Gemini Vision
            response = self.vision_model.generate_content([prompt, image])
            return response.text.strip()

        except Exception as e:
            raise Exception(f"Error analyzing image: {str(e)}")

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

            # AI Processing with Gemini Vision
            result_text = self.analyze_image(image_bytes, text_data.input_text.lower())
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
