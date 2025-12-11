# from fastapi import APIRouter, UploadFile, File, HTTPException
# from app.models.schemas import VideoUploadResponse, VideoStatus
# from app.controllers.video_controller import VideoController
# from app.core.exceptions import VideoUploadException
# import logging

# logger = logging.getLogger(__name__)
# router = APIRouter()
# video_controller = VideoController()

# @router.post("/videos/upload", response_model=VideoUploadResponse)
# async def upload_video(file: UploadFile = File(...)):
#     """
#     Upload a teaching video for analysis
    
#     - **file**: Video file (mp4, avi, mov, mkv)
#     """
#     try:
#         result = await video_controller.upload_video(file)
#         return result
#     except VideoUploadException as e:
#         raise HTTPException(status_code=e.status_code, detail=e.message)
#     except Exception as e:
#         logger.error(f"Unexpected error during upload: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")

# @router.get("/videos/{video_id}", response_model=VideoUploadResponse)
# async def get_video(video_id: str):
#     """
#     Get video metadata by ID
#     """
#     try:
#         result = await video_controller.get_video(video_id)
#         if not result:
#             raise HTTPException(status_code=404, detail="Video not found")
#         return result
#     except Exception as e:
#         logger.error(f"Error fetching video: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")

# @router.delete("/videos/{video_id}")
# async def delete_video(video_id: str):
#     """
#     Delete a video and its analysis results
#     """
#     try:
#         success = await video_controller.delete_video(video_id)
#         if not success:
#             raise HTTPException(status_code=404, detail="Video not found")
#         return {"message": "Video deleted successfully"}
#     except Exception as e:
#         logger.error(f"Error deleting video: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")

from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import VideoUploadResponse, VideoStatus
from app.controllers.video_controller import VideoController
from app.core.exceptions import VideoUploadException
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
video_controller = VideoController()

@router.post(
    "/videos/upload", 
    response_model=VideoUploadResponse,
    summary="Upload Video",
    description="""
    Upload a teaching video for analysis.
    
    **Supported Formats:**
    - MP4 (recommended)
    - AVI
    - MOV
    - MKV
    
    **Size Limit:** 500 MB
    
    **Returns:**
    - `video_id`: Use this ID to start analysis
    - `duration`: Video length in seconds
    - `size`: File size in bytes
    - `status`: Initially "uploaded"
    
    **Next Step:**
    After upload, call `/api/v1/analyze` with the returned `video_id`
    """,
    response_description="Video uploaded successfully with video ID"
)
async def upload_video(file: UploadFile = File(..., description="Video file to analyze")):
    """
    Upload a teaching video for analysis
    """
    try:
        result = await video_controller.upload_video(file)
        return result
    except VideoUploadException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error during upload: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get(
    "/videos/{video_id}", 
    response_model=VideoUploadResponse,
    summary="Get Video Metadata",
    description="""
    Retrieve metadata for an uploaded video.
    
    **Returns:**
    - Video ID, filename, size, duration
    - Upload timestamp
    - Current status (uploaded/processing/completed/failed)
    """,
    response_description="Video metadata"
)
async def get_video(video_id: str):
    """
    Get video metadata by ID
    """
    try:
        result = await video_controller.get_video(video_id)
        if not result:
            raise HTTPException(status_code=404, detail="Video not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching video: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete(
    "/videos/{video_id}",
    summary="Delete Video",
    description="""
    Delete a video and all associated analysis results.
    
    **Warning:** This action cannot be undone.
    
    Deletes:
    - Video file from storage
    - Video metadata from database
    - All analysis results for this video
    """,
    response_description="Video deleted successfully"
)
async def delete_video(video_id: str):
    """
    Delete a video and its analysis results
    """
    try:
        success = await video_controller.delete_video(video_id)
        if not success:
            raise HTTPException(status_code=404, detail="Video not found")
        return {"message": "Video deleted successfully", "video_id": video_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting video: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")