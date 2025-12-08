from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import VideoUploadResponse, VideoStatus
from app.controllers.video_controller import VideoController
from app.core.exceptions import VideoUploadException
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
video_controller = VideoController()

@router.post("/videos/upload", response_model=VideoUploadResponse)
async def upload_video(file: UploadFile = File(...)):
    """
    Upload a teaching video for analysis
    
    - **file**: Video file (mp4, avi, mov, mkv)
    """
    try:
        result = await video_controller.upload_video(file)
        return result
    except VideoUploadException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error during upload: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/videos/{video_id}", response_model=VideoUploadResponse)
async def get_video(video_id: str):
    """
    Get video metadata by ID
    """
    try:
        result = await video_controller.get_video(video_id)
        if not result:
            raise HTTPException(status_code=404, detail="Video not found")
        return result
    except Exception as e:
        logger.error(f"Error fetching video: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/videos/{video_id}")
async def delete_video(video_id: str):
    """
    Delete a video and its analysis results
    """
    try:
        success = await video_controller.delete_video(video_id)
        if not success:
            raise HTTPException(status_code=404, detail="Video not found")
        return {"message": "Video deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting video: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")