from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from app.models.schemas import AnalysisResult
from app.controllers.complete_analysis_controller import CompleteAnalysisController
from app.core.exceptions import VideoUploadException
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
controller = CompleteAnalysisController()

@router.post(
    "/analyze-video", 
    response_model=AnalysisResult,
    summary="Upload & Analyze Video (Complete)",
    description="""
    **🎯 One-Stop Video Analysis**
    
    Upload a video and get complete analysis results immediately in one call.
    No polling, no waiting - results returned directly!
    
    **📊 Complete Analysis Includes:**
    - ✅ Full transcript (Whisper AI)
    - ✅ Communication metrics (speaking rate, pauses, pitch, volume)
    - ✅ Engagement metrics (Q&A, questions, interactions)
    - ✅ **Technical Depth with Gemini AI** (concepts, domain, correctness)
    - ✅ Clarity metrics (video/audio quality, eye contact)
    - ✅ Interaction metrics (gestures, pose stability)
    - ✅ Overall weighted score (0-100)
    
    **⏱️ Processing Time:** 60-120 seconds
    
    **📝 Optional Context:**
    Provide context for better Gemini AI analysis:
    ```
    "Object-Oriented Programming lecture covering classes, objects, 
     methods, encapsulation with practical examples"
    ```
    
    **📤 Request:**
    - `file`: Video file (MP4, AVI, MOV, MKV)
    - `context`: Optional description for better AI analysis
    
    **📥 Response:**
    Complete analysis results with all metrics and scores immediately!
    
    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/analyze-video" \\
      -F "file=@lecture.mp4" \\
      -F "context=DSA lecture on Binary Search"
    ```
    
    **Use Cases:**
    - Single complete video analysis
    - Need Gemini AI technical depth
    - Want immediate results
    - Don't need parallel processing
    """,
    response_description="Complete analysis results with all metrics"
)
async def upload_and_analyze_video(
    file: UploadFile = File(..., description="Video file to analyze"),
    context: Optional[str] = Form(None, description="Optional context for better AI analysis")
):
    """
    Upload video and get complete analysis results immediately
    """
    try:
        logger.info(f"📹 New video analysis request: {file.filename}")
        
        result = await controller.upload_and_analyze(file, context)
        
        logger.info(f"✅ Analysis completed: {result.analysis_id}")
        
        return result
    
    except VideoUploadException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get(
    "/results/{identifier}", 
    response_model=AnalysisResult,
    summary="Get Analysis Results",
    description="""
    Retrieve analysis results by analysis ID or video ID.
    
    **Works with:**
    - Analysis ID (returned from upload & analyze)
    - Video ID (if you have the original video ID)
    
    **Use this to:**
    - Retrieve results later
    - Check previously analyzed videos
    - Get results without re-analyzing
    
    **Example:**
    ```bash
    # By analysis ID
    curl http://localhost:8000/api/v1/results/507f1f77bcf86cd799439012
    
    # By video ID
    curl http://localhost:8000/api/v1/results/507f1f77bcf86cd799439011
    ```
    """,
    response_description="Complete analysis results"
)
async def get_results(identifier: str):
    """
    Get analysis results by analysis ID or video ID
    """
    try:
        # Try as analysis ID first
        result = await controller.get_analysis_by_id(identifier)
        
        # If not found, try as video ID
        if not result:
            result = await controller.get_analysis_by_video_id(identifier)
        
        if not result:
            raise HTTPException(
                status_code=404, 
                detail=f"No analysis found for ID: {identifier}"
            )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching results: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch results")