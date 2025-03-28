from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from core.deps import get_db
from .model import TextData
from .schema import SummarizationCreate, SummarizationResponse
import time
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

class SummarizationRepository:
    def __init__(self):
        # Configure Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-2.0-flash')
 
    def create_text(self, text_data: SummarizationCreate, db: Session = Depends(get_db)) -> SummarizationResponse:
        """
        Create a new text entry, store it in the database, process it with AI, and update the result.

        Args:
            text_data (TextCreate): Input text from the user (topic/book name).
            db (Session): Database session.

        Returns:
            TextResponse: The stored text entry with AI-processed results.
        """
        new_text = TextData(input_text=text_data.input_text, result_text=None)
        db.add(new_text)
        db.commit()
        db.refresh(new_text)

        # AI Processing with Gemini
        try:
            # First, get comprehensive information about the topic
            research_prompt = f"""
            You are a research expert. Please provide a comprehensive overview of: {text_data.input_text}
            Focus on the key concepts, main ideas, and practical applications.
            
            Information:
            """
            
            research_response = self.model.generate_content(research_prompt)
            topic_content = research_response.text.strip()

            # Then, create an accessible summary
            summary_prompt = f"""
            You are an expert at creating accessible summaries for blind people. 
            Create a 3-4 line summary that captures the essence of the following information.
            Each line should focus on a different aspect:
            1. Main concept/idea
            2. Key principles or methods
            3. Practical application or impact
            Make it expressive, memorable, and impactful while keeping it simple and clear.
            
            Information to summarize:
            {topic_content}
            
            Summary:
            """
            
            response = self.model.generate_content(summary_prompt)
            result_text = response.text.strip()
            new_text.result_text = result_text
            db.commit()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

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
        Process topic/book name using Gemini AI for summarization.

        Args:
            text (str): The topic or book name to summarize.

        Returns:
            str: The AI-processed output.
        """
        try:
            # First, get comprehensive information about the topic
            research_prompt = f"""
            You are a research expert. Please provide a concise but comprehensive overview of: {text}
            Focus on the most impactful and essential information only.
            
            Information:
            """
            
            research_response = self.model.generate_content(research_prompt)
            topic_content = research_response.text.strip()

            # Then, create an accessible summary
            summary_prompt = f"""
            You are an expert at creating accessible summaries for blind people. 
            Create a single, powerful line that captures the essence of the following information.
            Make it expressive, memorable, and impactful while keeping it simple and clear.
            
            Information to summarize:
            {topic_content}
            
            Summary:
            """
            
            response = self.model.generate_content(summary_prompt)
            return response.text.strip()
        except Exception as e:
            raise Exception(f"Error generating summary: {str(e)}")
