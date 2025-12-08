from fastapi import UploadFile
from app.config import settings
from app.core.exceptions import VideoUploadException
import os
import uuid
import aiofiles
import cv2
import logging

logger = logging.getLogger(__name__)

class FileHandler:
    def __init__(self):
        self.upload_folder = settings.UPLOAD_FOLDER
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def validate_video_file(self, file: UploadFile):
        """Validate uploaded video file"""
        # Check extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise VideoUploadException(
                f"Invalid file type. Allowed: {settings.ALLOWED_EXTENSIONS}",
                status_code=400
            )
        
        # Check content type (guard if content_type is missing)
        if not file.content_type or not file.content_type.startswith('video/'):
            raise VideoUploadException(
                "File must be a video",
                status_code=400
            )
    
    async def save_upload_file(self, file: UploadFile) -> str:
        """Save uploaded file to disk"""
        try:
            # Generate unique filename
            file_ext = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            file_path = os.path.join(self.upload_folder, unique_filename)
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as out_file:
                content = await file.read()
                
                # Check size
                if len(content) > settings.MAX_VIDEO_SIZE:
                    raise VideoUploadException(
                        f"File too large. Max size: {settings.MAX_VIDEO_SIZE / (1024*1024)}MB",
                        status_code=413
                    )
                
                await out_file.write(content)
            
            logger.info(f"File saved: {file_path}")
            return file_path
        
        except VideoUploadException:
            raise
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise VideoUploadException(f"Failed to save file: {str(e)}")
    
    def get_video_duration(self, file_path: str) -> float:
        """Get video duration in seconds"""
        try:
            cap = cv2.VideoCapture(file_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            cap.release()
            return round(duration, 2)
        except Exception as e:
            logger.warning(f"Could not get video duration: {e}")
            return 0.0