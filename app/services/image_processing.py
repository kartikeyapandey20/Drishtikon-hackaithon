import os
import time
import base64
from typing import Dict, Any, Optional, List, Tuple
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from loguru import logger
import json
import httpx
from PIL import Image as PILImage
from io import BytesIO
from app.core.config import settings
from app.services.storage import storage_service
from app.models.image_processing import (
    Image, ProcessingResult, ProcessingStatus, ProcessingMode, ImageType
)
from app.schemas.image_processing import ProcessingCreate, ImageCreate


class ImageProcessingService:
    """Service to handle image processing with VLM and LLM."""
    
    def __init__(self):
        """Initialize image processing service."""
        self.vlm_provider = settings.VISION_MODEL_PROVIDER
        self.vlm_model = settings.VISION_MODEL_NAME
        self.llm_provider = settings.LLM_PROVIDER
        self.llm_model = settings.LLM_MODEL_NAME
        self.llm_temperature = settings.LLM_TEMPERATURE
        self.llm_max_tokens = settings.LLM_MAX_TOKENS
        
        # Initialize API keys
        self.openai_api_key = settings.OPENAI_API_KEY
        self.google_api_key = settings.GOOGLE_API_KEY
        self.huggingface_api_key = settings.HUGGINGFACE_API_KEY
        
        # Initialize prompt templates
        self._initialize_prompt_templates()
    
    def _initialize_prompt_templates(self):
        """Initialize prompt templates for different processing modes."""
        self.prompt_templates = {
            ProcessingMode.DESCRIPTION: {
                "vlm": "Describe this image in detail.",
                "llm": """
                    You are an assistant for visually impaired people.
                    Analyze the following image description and provide a clear,
                    concise, and informative response that helps the user understand
                    what's in the image.
                    
                    Image description:
                    {vlm_description}
                    
                    Provide your response in a way that is easy to understand for
                    someone who cannot see. Focus on the most important aspects first.
                """
            },
            ProcessingMode.OCR: {
                "vlm": "Read and extract all text visible in this image. Output the text exactly as it appears.",
                "llm": """
                    You are an assistant for visually impaired people.
                    The user has uploaded an image containing text, and a vision model
                    has extracted the following text content:
                    
                    {vlm_description}
                    
                    Please format this text in a clean, structured way. 
                    Correct any obvious OCR errors, but preserve the original meaning.
                    Organize it into paragraphs, bullet points, or sections if appropriate.
                    If there appears to be formatting like tables, try to represent that structure.
                """
            },
            ProcessingMode.SCENE_ANALYSIS: {
                "vlm": "Analyze this scene in detail. Identify all objects, people, activities, and environmental details.",
                "llm": """
                    You are an assistant for visually impaired people.
                    The user has uploaded an image of a scene, and a vision model
                    has provided the following analysis:
                    
                    {vlm_description}
                    
                    Please provide:
                    1. A concise summary of the scene (1-2 sentences)
                    2. Key elements in the scene (people, objects, etc.)
                    3. Spatial relationships between elements
                    4. Relevant context or activities occurring
                    5. Any potential hazards or important information for navigation
                    
                    Format your response in a way that provides the most crucial information first,
                    followed by details, in a clear and structured manner.
                """
            },
            ProcessingMode.DOCUMENT_READING: {
                "vlm": "This image contains a document. Extract all text, preserve formatting, and describe any non-text elements like logos or signatures.",
                "llm": """
                    You are an assistant for visually impaired people.
                    The user has uploaded an image of a document, and a vision model
                    has extracted the following content:
                    
                    {vlm_description}
                    
                    Please:
                    1. Format the document content clearly with appropriate structure
                    2. Identify the type of document if possible
                    3. Highlight key information (dates, amounts, signatures, etc.)
                    4. Summarize any non-text elements that were mentioned
                    
                    Present the information in a logical, structured way that makes the document
                    content accessible and easy to understand.
                """
            },
            ProcessingMode.ACCESSIBILITY: {
                "vlm": "Describe this image for a visually impaired person. Focus on essential details and any information that would be important for understanding the context.",
                "llm": """
                    You are an accessibility assistant for visually impaired people.
                    The user has uploaded an image, and a vision model has provided
                    the following description:
                    
                    {vlm_description}
                    
                    Please create an accessible description that:
                    1. Starts with the most essential information
                    2. Is concise but complete
                    3. Provides spatial and contextual information
                    4. Describes important colors, expressions, or details when relevant
                    5. Avoids unnecessary details
                    6. Uses clear, straightforward language
                    
                    Your goal is to give the user a clear mental image that communicates the
                    same information a sighted person would get from glancing at the image.
                """
            },
            # Add specialized processing modes
            "currency_recognition": {
                "vlm": """
                Analyze this image as if you're helping a visually impaired person identify currency.
                Identify:
                1. The type of currency (e.g., US Dollar, Euro, etc.)
                2. The denomination (e.g., $1, $5, €10, etc.)
                3. Visual markers that help identify the note (e.g., color, size, unique features)
                4. Any security features visible

                Provide a clear, concise description that would help someone who cannot see verify what currency they're holding.
                """,
                "llm": """
                    You are a specialized assistant for visually impaired people.
                    The user has uploaded an image of currency, and a vision model has provided
                    the following analysis:
                    
                    {vlm_description}
                    
                    Please structure the information in the following way:
                    1. Currency type and denomination (at the beginning)
                    2. Key identifying features, especially tactile ones
                    3. Security features that can be felt or seen under different conditions
                    4. Any additional verification methods
                    
                    Prioritize information that would be most useful for someone who cannot see to
                    confidently identify the currency they're holding.
                """
            },
            "color_analysis": {
                "vlm": """
                Analyze this image focusing exclusively on colors for a visually impaired person.
                Identify:
                1. The dominant colors in the image (name them and describe their general location)
                2. The overall color scheme (warm, cool, monochromatic, complementary, etc.)
                3. The contrast level between elements
                4. Any color patterns or gradients
                
                Provide a clear, descriptive explanation of the colors in the image that would help
                someone who cannot see understand the color composition.
                """,
                "llm": """
                    You are a specialized color analyst for visually impaired people.
                    The user has uploaded an image, and a vision model has analyzed
                    the colors as follows:
                    
                    {vlm_description}
                    
                    Please reorganize this information to:
                    1. Name each significant color with its common name and location
                    2. Describe the emotional impact or mood created by the color scheme
                    3. Explain contrast relationships between elements
                    4. Relate colors to common references (e.g., "sky blue", "forest green")
                    
                    Make your description vivid and relatable for someone who may have limited
                    or no color vision, using analogies and comparisons where helpful.
                """
            },
            "object_recognition": {
                "vlm": """
                Analyze this image to identify objects and their spatial relationships for a visually impaired person.
                For each significant object, provide:
                1. What the object is
                2. Where it's located in the image (e.g., "top left", "center")
                3. Its approximate size relative to the image
                4. How it relates to other objects (e.g., "the cup is on the table", "the chair is to the right of the desk")
                
                Also identify:
                - The type of scene (indoor, outdoor, kitchen, office, etc.)
                - The general spatial layout
                - Any information that would be useful for navigation or orientation
                
                Present this information in a clear, structured way that would help someone who cannot see understand the spatial arrangement.
                """,
                "llm": """
                    You are a specialized spatial analyst for visually impaired people.
                    The user has uploaded an image, and a vision model has analyzed
                    the objects and their relationships as follows:
                    
                    {vlm_description}
                    
                    Please reorganize this information to provide:
                    1. A brief overview of the scene type and general layout
                    2. A systematic description of objects from most to least important
                    3. Clear spatial relationships using clock positions and distances
                    4. Navigation guidance if applicable
                    
                    Use consistent directional language and reference points to help the user
                    build a mental map of the scene.
                """
            },
            "face_recognition": {
                "vlm": """
                Analyze this image to identify people and faces for a visually impaired person.
                For each person visible, describe:
                1. Their position in the image
                2. Their apparent facial expression
                3. What they're wearing
                4. Any distinguishing features
                5. The context of the group if multiple people are present
                
                Provide a comprehensive description that would help someone who cannot see understand who is in the image,
                what they look like, and what the social context might be.
                """,
                "llm": """
                    You are a specialized face and expression analyst for visually impaired people.
                    The user has uploaded an image, and a vision model has analyzed
                    the people in the image as follows:
                    
                    {vlm_description}
                    
                    Please reorganize this information to:
                    1. Identify each person by position and distinctive features
                    2. Describe facial expressions and apparent emotions
                    3. Note clothing and appearance details that help identify individuals
                    4. Explain the apparent social context and relationships
                    
                    Focus on the emotional and social information conveyed through expressions
                    and body language that might be missed without vision.
                """
            },
            "product_identification": {
                "vlm": """
                Analyze this image to identify a product for a visually impaired person.
                Please identify:
                1. The product name and brand
                2. Any barcode or QR code visible (and if possible, the value)
                3. The type of product
                4. A description of the packaging
                5. For food items: nutrition information including calories, fat, carbs, protein
                6. For food items: list of ingredients and potential allergens
                
                Provide a clear, detailed description that would help someone who cannot see understand what product they're holding.
                """,
                "llm": """
                    You are a specialized product identification assistant for visually impaired people.
                    The user has uploaded an image of a product, and a vision model has analyzed
                    it as follows:
                    
                    {vlm_description}
                    
                    Please reorganize this information to provide:
                    1. Product identification (name, brand, type) at the beginning
                    2. Key packaging features that help with identification
                    3. Important consumer information (nutrition, ingredients, allergens)
                    4. Usage or preparation instructions if visible
                    5. Expiration dates or other time-sensitive information
                    
                    Prioritize information that would help the user confidently identify the product
                    and determine its usability for their needs.
                """
            },
            "hazard_detection": {
                "vlm": """
                Analyze this image to identify potential hazards for a visually impaired person.
                Please identify:
                1. Any obstacles, steps, uneven surfaces, or barriers
                2. Potential tripping or falling hazards
                3. Moving hazards like vehicles or bicycles
                4. Safe areas or paths for navigation
                5. Any warning signs or signals visible
                
                Rate each hazard's severity (low, medium, high) and provide clear location information.
                Give specific advice that would help someone who cannot see navigate this environment safely.
                """,
                "llm": """
                    You are a specialized safety assistant for visually impaired people.
                    The user has uploaded an image of an environment, and a vision model has
                    identified potential hazards as follows:
                    
                    {vlm_description}
                    
                    Please reorganize this information to:
                    1. Highlight critical safety concerns first (high severity hazards)
                    2. Provide clear location information for each hazard
                    3. Suggest safe navigation paths or alternatives
                    4. Mention relevant warning signs or signals
                    
                    Use directional language that doesn't rely on visual cues, and prioritize
                    information that would prevent accidents or injuries.
                """
            },
            "transport_information": {
                "vlm": """
                Analyze this image to identify public transportation information for a visually impaired person.
                Please identify:
                1. The type of transport (bus, train, subway, etc.)
                2. Route numbers, line colors, or service names
                3. Destinations or next stops
                4. Departure times
                5. Platform or stop numbers
                6. Any other relevant information like delays or service changes
                7. Important symbols or icons visible
                
                Read all text visible on signs, displays, or the vehicle itself.
                Provide a clear, structured description that would help someone who cannot see navigate public transportation.
                """,
                "llm": """
                    You are a specialized public transport assistant for visually impaired people.
                    The user has uploaded an image related to public transportation, and a vision
                    model has extracted the following information:
                    
                    {vlm_description}
                    
                    Please reorganize this information to provide:
                    1. Transport type and identifier (route/line) at the beginning
                    2. Destination and next stop information
                    3. Timing information (departures, estimated arrival)
                    4. Platform/location information
                    5. Any service alerts or changes
                    
                    Present the information in order of urgency/importance for someone navigating
                    the transport system without visual cues.
                """
            },
            "medicine_identification": {
                "vlm": """
                Analyze this image to identify medication for a visually impaired person.
                Please describe in detail:
                1. The name of the medication if identifiable
                2. The form (pill, capsule, tablet, liquid, etc.)
                3. Color, shape, size and any markings or imprints
                4. Any visible text on packaging including manufacturer
                5. Any dosage information visible
                6. Any warning labels or special instructions visible
                
                Provide a clear, detailed description that would help someone who cannot see identify their medication safely.
                IMPORTANT: If you are not certain about the identification, clearly state this and focus on describing the physical characteristics.
                """,
                "llm": """
                    You are a specialized medication identification assistant for visually impaired people.
                    The user has uploaded an image of medication, and a vision model has analyzed
                    it as follows:
                    
                    {vlm_description}
                    
                    Please reorganize this information to provide:
                    1. Medication identification (name, strength) if confident
                    2. Physical characteristics (color, shape, markings)
                    3. Packaging details that help with identification
                    4. Dosage information if visible
                    5. Important warnings or instructions
                    
                    IMPORTANT: Emphasize safety. If there is any uncertainty about the identification,
                    clearly state this and focus on physical characteristics without making definitive claims.
                    Recommend consultation with a pharmacist or healthcare provider when appropriate.
                """
            },
            "emotional_analysis": {
                "vlm": """
                Analyze this image to identify the emotions of people for a visually impaired person.
                For each person visible, describe:
                1. Their position in the image so they can be identified
                2. Their primary emotion (happy, sad, angry, surprised, fearful, disgusted, neutral, etc.)
                3. Any secondary emotions that might be present
                4. Visual cues that indicate these emotions (facial expressions, body language, gestures)
                5. The social context of the scene and the emotional tone of the group if multiple people
                
                Provide a clear, nuanced description that would help someone who cannot see understand the emotional states and social dynamics.
                """,
                "llm": """
                    You are a specialized emotion and social dynamics analyst for visually impaired people.
                    The user has uploaded an image with people, and a vision model has analyzed
                    their emotional expressions as follows:
                    
                    {vlm_description}
                    
                    Please reorganize this information to:
                    1. Identify each person's location and distinguishing features
                    2. Describe their emotional states and the visual cues that indicate them
                    3. Explain the apparent social dynamics between people
                    4. Provide context about the overall emotional tone of the scene
                    
                    Focus on the subtle social and emotional information that would normally be
                    conveyed visually, using specific descriptions of facial expressions and body language.
                """
            },
            "image_comparison": {
                "vlm": """
                Compare these two images for a visually impaired person.
                
                For the first image: Describe the key elements, objects, people, colors, and overall scene.
                For the second image: Describe the key elements in the same way.
                
                Then provide a detailed comparison:
                1. Overall similarity level between the images
                2. Specific differences in objects, people, positions, colors, lighting, etc.
                3. Any temporal changes (if they appear to be the same scene at different times)
                4. If one image appears to be newer than the other
                
                Provide a clear, structured comparison that would help someone who cannot see understand how these images relate to each other.
                """,
                "llm": """
                    You are a specialized image comparison assistant for visually impaired people.
                    The user has uploaded two images for comparison, and a vision model has
                    analyzed them as follows:
                    
                    {vlm_description}
                    
                    Please reorganize this information to:
                    1. Summarize the key elements in each image separately
                    2. Highlight the most significant similarities
                    3. Emphasize the most notable differences
                    4. Explain any temporal or contextual relationship between the images
                    
                    Focus on providing a clear understanding of how these images relate to each other
                    and what key differences would be immediately apparent to someone with vision.
                """
            },
            "document_summarization": {
                "vlm": """
                Analyze this document image for a visually impaired person.
                Please:
                1. Extract all text visible in the document
                2. Identify the document type (letter, form, receipt, article, etc.)
                3. Determine the logical reading order of sections/paragraphs
                4. Create a concise summary of the key information
                5. List the 3-5 most important points
                6. Estimate reading time for the full document
                
                Organize the information clearly, with headings for each section, to help someone who cannot see understand the document content efficiently.
                """,
                "llm": """
                    You are a specialized document analysis assistant for visually impaired people.
                    The user has uploaded an image of a document, and a vision model has
                    extracted and analyzed the content as follows:
                    
                    {vlm_description}
                    
                    Please reorganize this information to:
                    1. Identify the document type and purpose upfront
                    2. Provide a concise summary of the key information (1-3 sentences)
                    3. List the most important points in order of significance
                    4. Structure the full content in a logical reading order
                    5. Highlight any action items or deadlines
                    
                    Focus on making the document content accessible and easily navigable through
                    clear structure and prioritization of information.
                """
            },
            "audio_description": {
                "vlm": """
                Create an audio description of this image for a visually impaired person.
                
                Format your description specifically for text-to-speech reading:
                1. Structure sentences for clear listening (not reading)
                2. Mark points that should be emphasized with *asterisks*
                3. Indicate where pauses should occur with (pause)
                4. Start with the most important information
                5. Be specific about spatial relationships
                6. Avoid visual references like "as you can see" or "shown here"
                
                Also provide guidance on the ideal speaking speed for this description.
                """,
                "llm": """
                    You are a specialized audio description creator for visually impaired people.
                    The user has uploaded an image, and a vision model has provided
                    the following description:
                    
                    {vlm_description}
                    
                    Please transform this into a proper audio description by:
                    1. Restructuring for listening rather than reading
                    2. Adding emphasis markers (*word*) on key elements
                    3. Adding pause indicators (pause) at natural break points
                    4. Removing visual references
                    5. Using consistent spatial language
                    6. Including guidance on speaking pace
                    
                    Format the description so it would flow naturally when read aloud by
                    a text-to-speech system or human reader.
                """
            }
        }
    
    async def process_image(
        self,
        db: Session,
        file: UploadFile,
        user_id: Optional[int] = None,
        processing_mode: ProcessingMode = ProcessingMode.DESCRIPTION,
        custom_prompt: Optional[str] = None,
        image_params: Optional[ImageCreate] = None,
    ) -> Tuple[Image, ProcessingResult]:
        """
        Process an image using VLM and LLM.
        
        Args:
            db: Database session
            file: Uploaded image file
            user_id: User ID (optional)
            processing_mode: Processing mode
            custom_prompt: Custom prompt for VLM (optional)
            image_params: Additional image parameters (optional)
            
        Returns:
            Tuple of (Image object, ProcessingResult object)
            
        Raises:
            HTTPException: If image processing fails
        """
        try:
            # Save file to storage
            filename, file_path, file_size = await storage_service.save_file(file)
            
            # Get image dimensions
            width, height = await self._get_image_dimensions(file)
            
            # Create image record
            image = Image(
                filename=filename,
                file_path=file_path,
                file_size=file_size,
                mime_type=file.content_type or "application/octet-stream",
                width=width,
                height=height,
                user_id=user_id,
                image_type=image_params.image_type if image_params else ImageType.OTHER,
                description=image_params.description if image_params else None,
                tags=json.dumps(image_params.tags) if image_params and image_params.tags else None,
                location=json.dumps(image_params.location) if image_params and image_params.location else None,
                metadata=json.dumps(image_params.metadata) if image_params and image_params.metadata else None,
            )
            
            db.add(image)
            db.commit()
            db.refresh(image)
            
            # Create processing result record
            processing_result = ProcessingResult(
                image_id=image.id,
                status=ProcessingStatus.PROCESSING,
                mode=processing_mode,
                custom_prompt=custom_prompt,
            )
            
            db.add(processing_result)
            db.commit()
            db.refresh(processing_result)
            
            # Process the image asynchronously (in a real system, this would be a background task)
            # For simplicity, we're doing it synchronously here
            await self._process_with_models(db, image, processing_result, custom_prompt)
            
            return image, processing_result
        
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing image: {str(e)}",
            )
    
    async def _get_image_dimensions(self, file: UploadFile) -> Tuple[Optional[int], Optional[int]]:
        """
        Get image dimensions.
        
        Args:
            file: Image file
            
        Returns:
            Tuple of (width, height)
        """
        try:
            content = await file.read()
            img = PILImage.open(BytesIO(content))
            width, height = img.size
            await file.seek(0)  # Reset file position
            return width, height
        except Exception as e:
            logger.warning(f"Could not get image dimensions: {str(e)}")
            await file.seek(0)  # Reset file position
            return None, None
    
    async def _process_with_models(
        self,
        db: Session,
        image: Image,
        processing_result: ProcessingResult,
        custom_prompt: Optional[str] = None,
    ) -> None:
        """
        Process image with VLM and LLM models.
        
        Args:
            db: Database session
            image: Image object
            processing_result: ProcessingResult object
            custom_prompt: Custom prompt for VLM (optional)
        """
        try:
            # Select prompt template
            mode = processing_result.mode
            if mode == ProcessingMode.CUSTOM and custom_prompt:
                vlm_prompt = custom_prompt
            else:
                vlm_prompt = self.prompt_templates[mode]["vlm"]
            
            prompt_template = vlm_prompt
            processing_result.prompt_template = prompt_template
            
            # Process with VLM
            vlm_start_time = time.time()
            vlm_response = await self._process_with_vlm(image, vlm_prompt)
            vlm_processing_time = time.time() - vlm_start_time
            
            # Update processing result with VLM data
            processing_result.vlm_provider = self.vlm_provider
            processing_result.vlm_model = self.vlm_model
            processing_result.vlm_response = vlm_response
            processing_result.vlm_processing_time = vlm_processing_time
            
            # Process with LLM if not custom mode
            if mode != ProcessingMode.CUSTOM:
                llm_prompt = self.prompt_templates[mode]["llm"].format(vlm_description=vlm_response)
                
                llm_start_time = time.time()
                llm_response = await self._process_with_llm(llm_prompt)
                llm_processing_time = time.time() - llm_start_time
                
                # Update processing result with LLM data
                processing_result.llm_provider = self.llm_provider
                processing_result.llm_model = self.llm_model
                processing_result.llm_response = llm_response
                processing_result.llm_processing_time = llm_processing_time
                
                # Set final output to LLM response
                processing_result.final_output = llm_response
            else:
                # For custom mode, set final output to VLM response
                processing_result.final_output = vlm_response
            
            # Set confidence score (placeholder - in a real implementation, this would be from the model)
            processing_result.confidence_score = 0.9
            
            # Update status to completed
            processing_result.status = ProcessingStatus.COMPLETED
            
        except Exception as e:
            logger.error(f"Error processing with models: {str(e)}")
            processing_result.status = ProcessingStatus.FAILED
            processing_result.error_message = str(e)
        
        # Update the processing result in the database
        db.add(processing_result)
        db.commit()
        db.refresh(processing_result)
    
    async def _process_with_vlm(self, image: Image, prompt: str) -> str:
        """
        Process image with Vision Language Model.
        
        Args:
            image: Image object
            prompt: Prompt for the VLM
            
        Returns:
            VLM response text
            
        Raises:
            Exception: If VLM processing fails
        """
        # In a real implementation, this would call the appropriate VLM API
        # This is a mock implementation for demonstration purposes
        
        if self.vlm_provider == "openai":
            if not self.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            
            return await self._process_with_openai_vlm(image, prompt)
        
        elif self.vlm_provider == "google":
            if not self.google_api_key:
                raise ValueError("Google API key not configured")
            
            # Mock implementation
            logger.info(f"Processing with Google VLM: {self.vlm_model}")
            return "This is a mock response from Google VLM."
        
        elif self.vlm_provider == "huggingface":
            if not self.huggingface_api_key:
                raise ValueError("HuggingFace API key not configured")
            
            # Mock implementation
            logger.info(f"Processing with HuggingFace VLM: {self.vlm_model}")
            return "This is a mock response from HuggingFace VLM."
        
        else:
            raise ValueError(f"Unsupported VLM provider: {self.vlm_provider}")
    
    async def _process_with_openai_vlm(self, image: Image, prompt: str) -> str:
        """
        Process image with OpenAI VLM.
        
        Args:
            image: Image object
            prompt: Prompt for the VLM
            
        Returns:
            VLM response text
            
        Raises:
            Exception: If processing fails
        """
        try:
            # Get image path
            image_path = image.file_path
            if image_path.startswith("/storage/"):
                image_path = os.path.join(settings.STORAGE_PATH, image_path.replace("/storage/", ""))
            
            # Read image file
            with open(image_path, "rb") as img_file:
                img_data = img_file.read()
            
            # Encode image as base64
            base64_image = base64.b64encode(img_data).decode("utf-8")
            
            # Call OpenAI API with GPT-4 Vision
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.vlm_model,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{base64_image}",
                                            "detail": "high"
                                        }
                                    }
                                ]
                            }
                        ],
                        "max_tokens": 1000,
                    },
                )
            
            # Process response
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                error_detail = response.json().get("error", {}).get("message", "Unknown error")
                logger.error(f"OpenAI API error: {response.status_code}, {error_detail}")
                raise Exception(f"OpenAI API error: {error_detail}")
        
        except Exception as e:
            logger.error(f"Error processing with OpenAI VLM: {str(e)}")
            raise Exception(f"Error processing with OpenAI VLM: {str(e)}")
    
    async def _process_with_llm(self, prompt: str) -> str:
        """
        Process text with Language Model.
        
        Args:
            prompt: Prompt for the LLM
            
        Returns:
            LLM response text
            
        Raises:
            Exception: If LLM processing fails
        """
        # In a real implementation, this would call the appropriate LLM API
        # This is a mock implementation for demonstration purposes
        
        if self.llm_provider == "openai":
            if not self.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            
            return await self._process_with_openai_llm(prompt)
        
        elif self.llm_provider == "google":
            if not self.google_api_key:
                raise ValueError("Google API key not configured")
            
            # Mock implementation
            logger.info(f"Processing with Google LLM: {self.llm_model}")
            return "This is a mock response from Google LLM."
        
        elif self.llm_provider == "huggingface":
            if not self.huggingface_api_key:
                raise ValueError("HuggingFace API key not configured")
            
            # Mock implementation
            logger.info(f"Processing with HuggingFace LLM: {self.llm_model}")
            return "This is a mock response from HuggingFace LLM."
        
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
    
    async def _process_with_openai_llm(self, prompt: str) -> str:
        """
        Process text with OpenAI LLM.
        
        Args:
            prompt: Prompt for the LLM
            
        Returns:
            LLM response text
            
        Raises:
            Exception: If processing fails
        """
        try:
            # Call OpenAI API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.llm_model,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": self.llm_temperature,
                        "max_tokens": self.llm_max_tokens,
                    },
                )
            
            # Process response
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                error_detail = response.json().get("error", {}).get("message", "Unknown error")
                logger.error(f"OpenAI API error: {response.status_code}, {error_detail}")
                raise Exception(f"OpenAI API error: {error_detail}")
        
        except Exception as e:
            logger.error(f"Error processing with OpenAI LLM: {str(e)}")
            raise Exception(f"Error processing with OpenAI LLM: {str(e)}")


# Create singleton instance
image_processing_service = ImageProcessingService() 