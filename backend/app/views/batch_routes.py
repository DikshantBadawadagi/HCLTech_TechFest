# from fastapi import APIRouter, UploadFile, File, Form, HTTPException
# from typing import List, Optional
# from app.models.batch_schemas import BatchAnalysisResponse
# from app.controllers.batch_controller import BatchController
# from app.core.exceptions import VideoUploadException
# import logging

# logger = logging.getLogger(__name__)
# router = APIRouter()
# batch_controller = BatchController()

# @router.post("/analyze-batch", response_model=BatchAnalysisResponse)
# async def analyze_batch(
#     files: List[UploadFile] = File(..., description="Multiple video chunks to analyze"),
#     context: Optional[str] = Form(None, description="Optional context for all chunks")
# ):
#     """
#     Analyze multiple video chunks in parallel using thread-based processing
    
#     **Features:**
#     - Thread-based parallel processing (4 chunks simultaneously)
#     - Works with uneven chunk sizes
#     - No Gemini API (avoids rate limits)
#     - Returns complete analysis for each chunk
    
#     **Analysis includes:**
#     - Transcript (Whisper)
#     - Communication metrics (speaking rate, pauses, pitch, volume)
#     - Engagement metrics (Q&A, questions, interactions)
#     - Clarity metrics (video quality, audio quality, eye contact)
#     - Interaction metrics (gestures, pose stability)
    
#     **Example:**
#     ```
#     files: [chunk1.mp4, chunk2.mp4, chunk3.mp4]
#     context: "Mathematics lecture on calculus"
#     ```
    
#     **Returns:**
#     ```json
#     {
#       "batch_id": "uuid",
#       "total_chunks": 3,
#       "successful_chunks": 3,
#       "failed_chunks": 0,
#       "status": "completed",
#       "total_processing_time": 45.2,
#       "average_chunk_time": 52.1,
#       "results": [
#         {
#           "chunk_id": "chunk_1",
#           "video_id": "...",
#           "transcript": "...",
#           "communication": {...},
#           "engagement": {...},
#           "clarity": {...},
#           "interaction": {...},
#           "overall_score": 75.5
#         },
#         ...
#       ]
#     }
#     ```
#     """
    
#     if not files or len(files) == 0:
#         raise HTTPException(status_code=400, detail="No files provided")
    
#     if len(files) > 20:
#         raise HTTPException(status_code=400, detail="Maximum 20 chunks allowed per batch")
    
#     try:
#         logger.info(f"📦 Batch analysis request received: {len(files)} chunks")
        
#         result = await batch_controller.process_batch(files, context)
        
#         logger.info(f"✅ Batch analysis completed: {result.batch_id}")
        
#         return result
    
#     except VideoUploadException as e:
#         raise HTTPException(status_code=e.status_code, detail=e.message)
#     except Exception as e:
#         logger.error(f"Batch analysis failed: {e}")
#         raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")

# @router.get("/batch/{batch_id}", response_model=BatchAnalysisResponse)
# async def get_batch_results(batch_id: str):
#     """
#     Retrieve batch analysis results by batch ID
    
#     **Args:**
#     - batch_id: The batch ID returned from analyze-batch
    
#     **Returns:**
#     Complete batch analysis response with all chunk results
#     """
#     try:
#         result = await batch_controller.get_batch_results(batch_id)
        
#         if not result:
#             raise HTTPException(status_code=404, detail="Batch not found")
        
#         return result
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error fetching batch results: {e}")
#         raise HTTPException(status_code=500, detail="Failed to fetch batch results")

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body
from typing import List, Optional
from app.models.batch_schemas import BatchAnalysisResponse
from app.controllers.batch_controller import BatchController
from app.core.exceptions import VideoUploadException
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()
batch_controller = BatchController()

@router.post(
    "/analyze-batch", 
    response_model=BatchAnalysisResponse,
    summary="Batch Analyze Multiple Video Chunks",
    description="""
    Analyze multiple video chunks in parallel using process-based parallelization.
    
    **Supports both FILE UPLOADS and CLOUD URLs:**
    - 📤 Local MP4 files
    - ☁️ S3 URLs
    - ☁️ Cloudinary URLs
    - ☁️ Any direct video URL
    
    **🚀 Performance:**
    - **3x faster** than sequential processing
    - Processes 3 chunks simultaneously
    - Process-based (Whisper-safe, no thread conflicts)
    
    **⚡ Features:**
    - Parallel processing of all chunks
    - Handles uneven chunk sizes
    - No Gemini API (avoids rate limits)
    - Complete analysis per chunk
    
    **📊 Analysis Includes:**
    - ✅ Transcript (Whisper via Groq Cloud)
    - ✅ Communication metrics
    - ✅ Engagement metrics
    - ✅ Clarity metrics
    - ✅ Interaction metrics
    - ❌ Technical Depth (skipped to avoid Gemini rate limits)
    
    **📝 Request Formats:**
    
    **Option 1: File Upload (Multipart)**
    ```bash
    curl -X POST /api/v1/batch/analyze-batch \\
      -F "files=@chunk1.mp4" \\
      -F "files=@chunk2.mp4" \\
      -F "context=Mathematics lecture"
    ```
    
    **Option 2: Cloud URLs (JSON)**
    ```bash
    curl -X POST /api/v1/batch/analyze-batch-urls \\
      -H "Content-Type: application/json" \\
      -d '{
        "urls": [
          "https://s3.amazonaws.com/videos/chunk1.mp4",
          "https://res.cloudinary.com/videos/chunk2.mp4"
        ],
        "context": "Data Structures lecture"
      }'
    ```
    
    **Option 3: Mixed (Files + URLs) - Coming Soon**
    
    **⏱️ Processing Time:**
    - 3 chunks × 30s each → ~65-70s total (sequential: 180s)
    - Speedup: ~2.5-3x
    - Time ≈ longest chunk duration + overhead
    
    **📤 Response:**
    - Individual results for each chunk
    - Success/failure status per chunk
    - Overall batch statistics
    - Batch ID for later retrieval
    - Source tracking (upload vs URL)
    """,
    response_description="Complete batch analysis with all chunk results"
)
async def analyze_batch(
    files: List[UploadFile] = File(
        default=None, 
        description="Multiple video chunks (max 20) via file upload",
        example=["chunk1.mp4", "chunk2.mp4", "chunk3.mp4"]
    ),
    context: Optional[str] = Form(
        None, 
        description="Optional context for all chunks",
        example="Data Structures and Algorithms lecture series covering sorting algorithms"
    )
):
    """
    Analyze multiple video chunks in parallel (3 simultaneous processes)
    
    Use file uploads for local videos
    """
    
    try:
        logger.info(f"📦 Batch analysis request received: {len(files) if files else 0} files")
        
        result = await batch_controller.process_batch(files=files, context=context)
        
        logger.info(f"✅ Batch analysis completed: {result.batch_id}")
        
        return result
    
    except VideoUploadException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Batch analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")

@router.post(
    "/analyze-batch-urls",
    response_model=BatchAnalysisResponse,
    summary="Batch Analyze Videos from Cloud URLs",
    description="""
    Analyze multiple videos from cloud URLs (S3, Cloudinary, etc.) in parallel.
    
    **✨ Cloud Provider Support:**
    - ☁️ AWS S3
    - ☁️ Cloudinary
    - ☁️ Google Cloud Storage
    - ☁️ Azure Blob Storage
    - ☁️ Any direct HTTPS video URL
    
    **🚀 Advantages:**
    - No local storage needed
    - Direct cloud-to-processing pipeline
    - Automatic cleanup after analysis
    - Perfect for high-volume processing
    
    **📝 Request Example:**
    ```json
    {
      "urls": [
        "https://s3.amazonaws.com/bucket/video1.mp4",
        "https://res.cloudinary.com/account/video/video2.mp4",
        "https://storage.googleapis.com/bucket/video3.mp4"
      ],
      "context": "Advanced Python Programming Course - Modules 3-5"
    }
    ```
    
    **✅ What You Get:**
    - Same analysis as file uploads
    - Individual results per URL
    - Source URL tracked in response
    - Parallel processing (3 concurrent downloads+analysis)
    - Automatic error handling per video
    
    **⏱️ Performance:**
    - Download + Transcribe + Analyze in parallel
    - 3 videos processed simultaneously
    - Total time ≈ longest video duration + overhead
    
    **⚠️ Requirements:**
    - URLs must be directly accessible (no auth required for demo)
    - Videos must be in MP4, AVI, MOV, or MKV format
    - Max file size: 500MB per video
    - Must be public/accessible URLs
    """,
    response_description="Batch analysis results with source tracking"
)
async def analyze_batch_urls(
    request_body: dict = Body(
        ...,
        example={
            "urls": [
                "https://example.s3.amazonaws.com/video1.mp4",
                "https://example.s3.amazonaws.com/video2.mp4"
            ],
            "context": "Biology lecture - Photosynthesis"
        }
    )
):
    """
    Analyze multiple videos from cloud URLs in parallel
    """
    try:
        # Extract URLs and context from request body
        urls = request_body.get("urls") if isinstance(request_body, dict) else None
        context = request_body.get("context") if isinstance(request_body, dict) else None
        
        logger.info(f"🌐 URL batch request received:")
        logger.info(f"   URLs count: {len(urls) if urls else 0}")
        logger.info(f"   URLs type: {type(urls)}")
        logger.info(f"   Context: {context}")
        
        if not urls or len(urls) == 0:
            raise HTTPException(
                status_code=400,
                detail="No URLs provided. Please include 'urls' array in request body."
            )
        
        # Ensure urls is a list
        if not isinstance(urls, list):
            raise HTTPException(
                status_code=400,
                detail="'urls' must be an array of strings"
            )
        
        if len(urls) > 20:
            raise HTTPException(
                status_code=400,
                detail="Maximum 20 videos allowed per batch. Please split into multiple requests."
            )
        
        logger.info(f"📦 Batch URL analysis request: {len(urls)} videos")
        
        result = await batch_controller.process_batch(urls=urls, context=context)
        
        logger.info(f"✅ Batch URL analysis completed: {result.batch_id}")
        
        return result
    
    except VideoUploadException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch URL analysis failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")

@router.get(
    "/batch/{batch_id}", 
    response_model=BatchAnalysisResponse,
    summary="Get Batch Results",
    description="""
    Retrieve batch analysis results by batch ID.
    
    **Returns:**
    - Complete batch statistics
    - Individual results for each chunk/URL
    - Success/failure counts
    - Processing times and speedup metrics
    - Source tracking (upload vs URL)
    
    **Use this to:**
    - Check batch status after submission
    - Retrieve results later
    - Get detailed per-chunk analysis
    - Track processing metrics
    """,
    response_description="Complete batch analysis results"
)
async def get_batch_results(batch_id: str):
    """
    Retrieve batch analysis results by batch ID
    """
    try:
        result = await batch_controller.get_batch_results(batch_id)
        
        if not result:
            raise HTTPException(
                status_code=404, 
                detail=f"Batch not found: {batch_id}"
            )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching batch results: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch batch results")