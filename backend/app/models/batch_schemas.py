from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.models.schemas import (
    CommunicationMetrics, EngagementMetrics, ClarityMetrics, InteractionMetrics
)

class ChunkUpload(BaseModel):
    """Single chunk in batch upload"""
    chunk_id: str
    # File will be uploaded via multipart form data

class ChunkUrl(BaseModel):
    """Single chunk from URL (S3, Cloudinary, etc.)"""
    chunk_id: str
    url: str = Field(..., description="Direct URL to video file (S3, Cloudinary, etc.)")

class BatchAnalysisRequest(BaseModel):
    """Request for batch analysis"""
    context: Optional[str] = Field(None, description="Optional context for all chunks")

class ChunkAnalysisResult(BaseModel):
    """Analysis result for a single chunk"""
    chunk_id: str
    video_id: str
    filename: str
    duration: float
    size: int
    source_type: str  # "upload" or "url"
    source_url: Optional[str] = None  # Original URL if downloaded from URL
    
    # Analysis results
    transcript: str
    transcript_confidence: float
    
    communication: CommunicationMetrics
    engagement: EngagementMetrics
    clarity: ClarityMetrics
    interaction: InteractionMetrics
    
    # Scores (no technical depth without Gemini)
    overall_score: float  # Weighted average of 4 metrics
    
    # Metadata
    processing_time: float
    status: str  # "success" or "failed"
    error_message: Optional[str] = None

class BatchAnalysisResponse(BaseModel):
    """Complete batch analysis response"""
    batch_id: str
    total_chunks: int
    successful_chunks: int
    failed_chunks: int
    status: str  # "completed", "partial", "failed"
    
    total_processing_time: float  # Wall clock time
    average_chunk_time: float
    
    results: List[ChunkAnalysisResult]
    
    created_at: datetime
    completed_at: datetime