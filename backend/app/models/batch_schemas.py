from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.models.schemas import (
    CommunicationMetrics, EngagementMetrics, ClarityMetrics, InteractionMetrics
)

class ChunkUpload(BaseModel):
    """Single chunk in batch upload"""
    chunk_id: str
    # File will be uploaded via multipart form data

class BatchAnalysisRequest(BaseModel):
    """Request for batch analysis"""
    context: Optional[str] = None  # Optional context for all chunks

class ChunkAnalysisResult(BaseModel):
    """Analysis result for a single chunk"""
    chunk_id: str
    video_id: str
    filename: str
    duration: float
    size: int
    
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