from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional
from app.models.batch_schemas import BatchAnalysisResponse
from app.controllers.batch_controller import BatchController
from app.core.exceptions import VideoUploadException
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
batch_controller = BatchController()

@router.post("/analyze-batch", response_model=BatchAnalysisResponse)
async def analyze_batch(
    files: List[UploadFile] = File(..., description="Multiple video chunks to analyze"),
    context: Optional[str] = Form(None, description="Optional context for all chunks")
):
    """
    Analyze multiple video chunks in parallel using thread-based processing
    
    **Features:**
    - Thread-based parallel processing (4 chunks simultaneously)
    - Works with uneven chunk sizes
    - No Gemini API (avoids rate limits)
    - Returns complete analysis for each chunk
    
    **Analysis includes:**
    - Transcript (Whisper)
    - Communication metrics (speaking rate, pauses, pitch, volume)
    - Engagement metrics (Q&A, questions, interactions)
    - Clarity metrics (video quality, audio quality, eye contact)
    - Interaction metrics (gestures, pose stability)
    
    **Example:**
    ```
    files: [chunk1.mp4, chunk2.mp4, chunk3.mp4]
    context: "Mathematics lecture on calculus"
    ```
    
    **Returns:**
    ```json
    {
      "batch_id": "uuid",
      "total_chunks": 3,
      "successful_chunks": 3,
      "failed_chunks": 0,
      "status": "completed",
      "total_processing_time": 45.2,
      "average_chunk_time": 52.1,
      "results": [
        {
          "chunk_id": "chunk_1",
          "video_id": "...",
          "transcript": "...",
          "communication": {...},
          "engagement": {...},
          "clarity": {...},
          "interaction": {...},
          "overall_score": 75.5
        },
        ...
      ]
    }
    ```
    """
    
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="No files provided")
    
    if len(files) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 chunks allowed per batch")
    
    try:
        logger.info(f"📦 Batch analysis request received: {len(files)} chunks")
        
        result = await batch_controller.process_batch(files, context)
        
        logger.info(f"✅ Batch analysis completed: {result.batch_id}")
        
        return result
    
    except VideoUploadException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Batch analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")

@router.get("/batch/{batch_id}", response_model=BatchAnalysisResponse)
async def get_batch_results(batch_id: str):
    """
    Retrieve batch analysis results by batch ID
    
    **Args:**
    - batch_id: The batch ID returned from analyze-batch
    
    **Returns:**
    Complete batch analysis response with all chunk results
    """
    try:
        result = await batch_controller.get_batch_results(batch_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching batch results: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch batch results")