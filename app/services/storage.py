import os
import uuid
from fastapi import UploadFile
import shutil
from typing import Tuple, Optional
from app.core.config import settings
from loguru import logger
import time
import mimetypes


class StorageService:
    """Service to handle file storage operations."""
    
    def __init__(self):
        """Initialize storage service based on configuration."""
        self.provider = settings.STORAGE_PROVIDER
        self.storage_path = settings.STORAGE_PATH
        
        # Ensure storage directory exists
        if self.provider == "local":
            os.makedirs(self.storage_path, exist_ok=True)
    
    async def save_file(self, file: UploadFile) -> Tuple[str, str, int]:
        """
        Save a file to storage.
        
        Args:
            file: UploadFile object
            
        Returns:
            Tuple of (filename, file_path, file_size)
            
        Raises:
            Exception: If file cannot be saved
        """
        if self.provider == "local":
            return await self._save_local(file)
        elif self.provider == "gcs":
            # Implementation for Google Cloud Storage
            raise NotImplementedError("Google Cloud Storage not yet implemented")
        elif self.provider == "s3":
            # Implementation for Amazon S3
            raise NotImplementedError("Amazon S3 not yet implemented")
        else:
            raise ValueError(f"Unsupported storage provider: {self.provider}")
    
    async def _save_local(self, file: UploadFile) -> Tuple[str, str, int]:
        """
        Save a file to local storage.
        
        Args:
            file: UploadFile object
            
        Returns:
            Tuple of (filename, file_path, file_size)
            
        Raises:
            Exception: If file cannot be saved
        """
        try:
            # Generate unique filename
            original_filename = file.filename
            extension = os.path.splitext(original_filename)[1] if original_filename else ""
            if not extension:
                # Try to guess extension from content type
                guessed_extension = mimetypes.guess_extension(file.content_type)
                extension = guessed_extension if guessed_extension else ".bin"
            
            timestamp = int(time.time())
            unique_filename = f"{timestamp}_{uuid.uuid4().hex}{extension}"
            file_path = os.path.join(self.storage_path, unique_filename)
            
            # Save the file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Return file details
            return original_filename, f"/storage/{unique_filename}", file_size
        
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            raise Exception(f"Could not save file: {str(e)}")
        
        finally:
            # Reset file position
            await file.seek(0)
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file was deleted, False otherwise
        """
        if self.provider == "local":
            return self._delete_local(file_path)
        elif self.provider == "gcs":
            # Implementation for Google Cloud Storage
            raise NotImplementedError("Google Cloud Storage not yet implemented")
        elif self.provider == "s3":
            # Implementation for Amazon S3
            raise NotImplementedError("Amazon S3 not yet implemented")
        else:
            raise ValueError(f"Unsupported storage provider: {self.provider}")
    
    def _delete_local(self, file_path: str) -> bool:
        """
        Delete a file from local storage.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file was deleted, False otherwise
        """
        try:
            # Extract filename from path
            if file_path.startswith("/storage/"):
                filename = file_path.replace("/storage/", "")
                full_path = os.path.join(self.storage_path, filename)
            else:
                full_path = file_path
            
            # Check if file exists
            if not os.path.exists(full_path):
                logger.warning(f"File not found: {full_path}")
                return False
            
            # Delete file
            os.remove(full_path)
            logger.info(f"Deleted file: {full_path}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False


# Create singleton instance
storage_service = StorageService() 