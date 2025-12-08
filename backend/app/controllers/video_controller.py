from fastapi import UploadFile
from app.models.schemas import VideoUploadResponse, VideoStatus
from app.utils.db_helper import get_database, get_fs_bucket
from app.utils.file_handler import FileHandler
from app.core.exceptions import VideoUploadException
from app.config import settings
from bson import ObjectId
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

class VideoController:
    def __init__(self):
        self.file_handler = FileHandler()
    
    async def upload_video(self, file: UploadFile) -> VideoUploadResponse:
        """Handle video upload and storage"""
        try:
            # Validate file
            self.file_handler.validate_video_file(file)
            
            # Save to uploads folder
            file_path = await self.file_handler.save_upload_file(file)
            
            # Get video metadata
            duration = self.file_handler.get_video_duration(file_path)
            file_size = os.path.getsize(file_path)
            
            # Store metadata in MongoDB
            db = get_database()
            video_doc = {
                "filename": file.filename,
                "file_path": file_path,
                "size": file_size,
                "duration": duration,
                "status": VideoStatus.UPLOADED,
                "uploaded_at": datetime.utcnow()
            }
            
            result = await db.videos.insert_one(video_doc)
            video_id = str(result.inserted_id)
            
            logger.info(f"Video uploaded successfully: {video_id}")
            
            return VideoUploadResponse(
                video_id=video_id,
                filename=file.filename,
                size=file_size,
                duration=duration,
                status=VideoStatus.UPLOADED,
                uploaded_at=video_doc["uploaded_at"]
            )
        
        except VideoUploadException:
            raise
        except Exception as e:
            logger.error(f"Error uploading video: {e}")
            raise VideoUploadException(f"Failed to upload video: {str(e)}")
    
    async def get_video(self, video_id: str) -> VideoUploadResponse:
        """Get video metadata"""
        try:
            db = get_database()
            video = await db.videos.find_one({"_id": ObjectId(video_id)})
            
            if not video:
                return None
            
            return VideoUploadResponse(
                video_id=str(video["_id"]),
                filename=video["filename"],
                size=video["size"],
                duration=video.get("duration"),
                status=VideoStatus(video["status"]),
                uploaded_at=video["uploaded_at"]
            )
        except Exception as e:
            logger.error(f"Error fetching video: {e}")
            raise
    
    async def delete_video(self, video_id: str) -> bool:
        """Delete video and cleanup"""
        try:
            db = get_database()
            video = await db.videos.find_one({"_id": ObjectId(video_id)})
            
            if not video:
                return False
            
            # Delete file
            if os.path.exists(video["file_path"]):
                os.remove(video["file_path"])
            
            # Delete from database
            await db.videos.delete_one({"_id": ObjectId(video_id)})
            await db.analysis_results.delete_many({"video_id": video_id})
            
            logger.info(f"Video deleted: {video_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting video: {e}")
            raise