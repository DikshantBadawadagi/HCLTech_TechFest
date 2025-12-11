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
#     - **context**: (Optional) Context about the video content
#       Example: "This is a DSA lecture on Binary Search covering O(log n) complexity, 
#                 implementation, and edge cases."
    
#     Returns analysis_id for tracking progress
#     """
#     try:
#         result = await analysis_controller.start_analysis(
#             request.video_id, 
#             background_tasks,
#             request.context
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

@router.post(
    "/analyze", 
    response_model=AnalysisResponse,
    summary="Analyze Complete Video",
    description="""
    Analyze a complete video with full AI-powered technical depth evaluation using Gemini.
    
    **Features:**
    - Complete transcript using Whisper
    - Communication analysis (speaking rate, pauses, pitch, volume)
    - Engagement metrics (Q&A, questions, interactions)
    - **Technical Depth with Gemini AI** (concepts, correctness, domain detection)
    - Clarity assessment (video/audio quality, eye contact)
    - Interaction analysis (gestures, pose stability)
    
    **Processing Time:** 60-120 seconds depending on video length
    
    **Includes:**
    - ✅ All 5 analysis categories
    - ✅ Gemini AI for technical depth
    - ✅ User context support
    - ✅ Full transcript
    - ✅ Overall weighted score
    
    **Example Request:**
    ```json
    {
        "video_id": "507f1f77bcf86cd799439011",
        "context": "Object-Oriented Programming lecture covering classes, objects, methods, and encapsulation with practical examples"
    }
    ```
    
    **Returns:**
    - `analysis_id`: Track analysis progress
    - `status`: "processing" initially
    - Use GET `/api/v1/analysis/{analysis_id}` to retrieve results
    """,
    response_description="Analysis started successfully with analysis ID for tracking"
)
async def start_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Start complete video analysis with Gemini technical depth
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

@router.get(
    "/analysis/{analysis_id}", 
    response_model=AnalysisResult,
    summary="Get Analysis Results",
    description="""
    Retrieve complete analysis results by analysis ID.
    
    **Response includes:**
    - Full transcript with confidence score
    - Communication metrics and score
    - Engagement metrics and score
    - Technical depth metrics and score (with Gemini AI analysis)
    - Clarity metrics and score
    - Interaction metrics and score
    - Overall weighted score (0-100)
    - Processing time
    - Status (processing/completed/failed)
    
    **Status Values:**
    - `processing`: Analysis in progress
    - `completed`: Analysis finished successfully
    - `failed`: Analysis encountered an error
    
    **Poll this endpoint** every 5 seconds while status is "processing"
    """,
    response_description="Complete analysis results with all metrics"
)
async def get_analysis_result(analysis_id: str):
    """
    Get complete analysis results including Gemini technical depth
    """
    try:
        result = await analysis_controller.get_analysis_result(analysis_id)
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching analysis: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get(
    "/analysis/video/{video_id}", 
    response_model=AnalysisResult,
    summary="Get Analysis by Video ID",
    description="""
    Retrieve analysis results using the original video ID.
    
    Useful when you have the video ID but not the analysis ID.
    Returns the most recent analysis for the given video.
    """,
    response_description="Complete analysis results for the video"
)
async def get_analysis_by_video(video_id: str):
    """
    Get analysis results by video ID
    """
    try:
        result = await analysis_controller.get_analysis_by_video(video_id)
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found for this video")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching analysis by video: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")