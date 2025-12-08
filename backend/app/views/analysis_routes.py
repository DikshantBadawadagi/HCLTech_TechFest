# from fastapi import APIRouter, HTTPException, BackgroundTasks
# from app.models.schemas import AnalysisRequest, AnalysisResponse, AnalysisResult
# from app.controllers.analysis_controller import AnalysisController
# from app.core.exceptions import AnalysisException
# import logging

# logger = logging.getLogger(__name__)
# router = APIRouter()
# analysis_controller = AnalysisController()

# @router.post("/analyze", response_model=AnalysisResponse)
# async def start_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
#     """
#     Start video analysis
    
#     - **video_id**: ID of the uploaded video
    
#     Returns analysis_id for tracking progress
#     """
#     try:
#         result = await analysis_controller.start_analysis(
#             request.video_id, 
#             background_tasks
#         )
#         return result
#     except AnalysisException as e:
#         raise HTTPException(status_code=e.status_code, detail=e.message)
#     except Exception as e:
#         logger.error(f"Error starting analysis: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")

# @router.get("/analysis/{analysis_id}", response_model=AnalysisResult)
# async def get_analysis_result(analysis_id: str):
#     """
#     Get analysis results by ID
#     """
#     try:
#         result = await analysis_controller.get_analysis_result(analysis_id)
#         if not result:
#             raise HTTPException(status_code=404, detail="Analysis not found")
#         return result
#     except Exception as e:
#         logger.error(f"Error fetching analysis: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")

# @router.get("/analysis/video/{video_id}", response_model=AnalysisResult)
# async def get_analysis_by_video(video_id: str):
#     """
#     Get analysis results by video ID
#     """
#     try:
#         result = await analysis_controller.get_analysis_by_video(video_id)
#         if not result:
#             raise HTTPException(status_code=404, detail="Analysis not found for this video")
#         return result
#     except Exception as e:
#         logger.error(f"Error fetching analysis by video: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")

from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.schemas import AnalysisRequest, AnalysisResponse, AnalysisResult
from app.controllers.analysis_controller import AnalysisController
from app.core.exceptions import AnalysisException
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
analysis_controller = AnalysisController()

@router.post("/analyze", response_model=AnalysisResponse)
async def start_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Start video analysis
    
    - **video_id**: ID of the uploaded video
    - **context**: (Optional) Context about the video content
      Example: "This is a DSA lecture on Binary Search covering O(log n) complexity, 
                implementation, and edge cases."
    
    Returns analysis_id for tracking progress
    """
    try:
        result = await analysis_controller.start_analysis(
            request.video_id, 
            background_tasks,
            request.context
        )
        return result
    except AnalysisException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error starting analysis: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/analysis/{analysis_id}", response_model=AnalysisResult)
async def get_analysis_result(analysis_id: str):
    """
    Get analysis results by ID
    """
    try:
        result = await analysis_controller.get_analysis_result(analysis_id)
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return result
    except Exception as e:
        logger.error(f"Error fetching analysis: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/analysis/video/{video_id}", response_model=AnalysisResult)
async def get_analysis_by_video(video_id: str):
    """
    Get analysis results by video ID
    """
    try:
        result = await analysis_controller.get_analysis_by_video(video_id)
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found for this video")
        return result
    except Exception as e:
        logger.error(f"Error fetching analysis by video: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")