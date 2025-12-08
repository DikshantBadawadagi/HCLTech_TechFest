# from pydantic import BaseModel, Field
# from typing import Optional, List, Dict
# from datetime import datetime
# from enum import Enum

# class VideoStatus(str, Enum):
#     UPLOADED = "uploaded"
#     PROCESSING = "processing"
#     COMPLETED = "completed"
#     FAILED = "failed"

# class VideoUploadResponse(BaseModel):
#     video_id: str
#     filename: str
#     size: int
#     duration: Optional[float] = None
#     status: VideoStatus
#     uploaded_at: datetime
#     context: Optional[str] = None  # User-provided context

# class AnalysisRequest(BaseModel):
#     video_id: str
#     context: Optional[str] = None  # Optional: "This is a DSA lecture on Binary Search covering time complexity..."

# class CommunicationMetrics(BaseModel):
#     speaking_rate: float  # words per minute
#     pause_count: int
#     avg_pause_duration: float
#     stuttering_count: int
#     volume_mean: float
#     volume_std: float
#     pitch_mean: float
#     pitch_std: float
#     score: float

# class EngagementMetrics(BaseModel):
#     qna_pairs: int
#     question_count: int
#     interaction_moments: int
#     rhetorical_questions: int = 0
#     direct_address_count: int = 0
#     score: float

# class TechnicalDepthMetrics(BaseModel):
#     concept_count: int
#     technical_terms: List[str]
#     domain: str = "general"
#     concept_correctness_score: float
#     depth_score: float
#     score: float
#     llm_analysis: Optional[str] = None  # Gemini's detailed analysis
#     context_provided: bool = False  # Whether user provided context

# class ClarityMetrics(BaseModel):
#     video_quality_score: float
#     audio_quality_score: float
#     energy_score: float
#     pitch_variation: float
#     eye_contact_percentage: float
#     score: float

# class InteractionMetrics(BaseModel):
#     eye_contact_duration: float
#     gesture_frequency: float
#     pose_stability: float
#     score: float

# class AnalysisResult(BaseModel):
#     analysis_id: str
#     video_id: str
#     status: VideoStatus
    
#     # Transcript
#     transcript: Optional[str] = None
#     transcript_confidence: Optional[float] = None
    
#     # Metrics
#     communication: Optional[CommunicationMetrics] = None
#     engagement: Optional[EngagementMetrics] = None
#     technical_depth: Optional[TechnicalDepthMetrics] = None
#     clarity: Optional[ClarityMetrics] = None
#     interaction: Optional[InteractionMetrics] = None
    
#     # Overall Score
#     overall_score: Optional[float] = None
    
#     # Metadata
#     processing_time: Optional[float] = None
#     created_at: datetime
#     completed_at: Optional[datetime] = None
#     error_message: Optional[str] = None

# class AnalysisResponse(BaseModel):
#     analysis_id: str
#     status: VideoStatus
#     message: str

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class VideoStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class VideoUploadResponse(BaseModel):
    video_id: str
    filename: str
    size: int
    duration: Optional[float] = None
    status: VideoStatus
    uploaded_at: datetime
    context: Optional[str] = None  # User-provided context

class AnalysisRequest(BaseModel):
    video_id: str
    context: Optional[str] = None  # Optional: "This is a DSA lecture on Binary Search covering time complexity..."

class CommunicationMetrics(BaseModel):
    speaking_rate: float  # words per minute
    pause_count: int
    avg_pause_duration: float
    stuttering_count: int
    volume_mean: float
    volume_std: float
    pitch_mean: float
    pitch_std: float
    score: float

class EngagementMetrics(BaseModel):
    qna_pairs: int
    question_count: int
    interaction_moments: int
    rhetorical_questions: int = 0
    direct_address_count: int = 0
    score: float

class TechnicalDepthMetrics(BaseModel):
    concept_count: int
    technical_terms: List[str]
    domain: str = "general"
    concept_correctness_score: float
    depth_score: float
    score: float
    llm_analysis: Optional[str] = None  # Gemini's detailed analysis
    context_provided: bool = False  # Whether user provided context
    
    class Config:
        # Allow extra fields for flexibility
        extra = "allow"

class ClarityMetrics(BaseModel):
    video_quality_score: float
    audio_quality_score: float
    energy_score: float
    pitch_variation: float
    eye_contact_percentage: float
    score: float

class InteractionMetrics(BaseModel):
    eye_contact_duration: float
    gesture_frequency: float
    pose_stability: float
    score: float

class AnalysisResult(BaseModel):
    analysis_id: str
    video_id: str
    status: VideoStatus
    
    # Transcript
    transcript: Optional[str] = None
    transcript_confidence: Optional[float] = None
    
    # Metrics
    communication: Optional[CommunicationMetrics] = None
    engagement: Optional[EngagementMetrics] = None
    technical_depth: Optional[TechnicalDepthMetrics] = None
    clarity: Optional[ClarityMetrics] = None
    interaction: Optional[InteractionMetrics] = None
    
    # Overall Score
    overall_score: Optional[float] = None
    
    # Metadata
    processing_time: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class AnalysisResponse(BaseModel):
    analysis_id: str
    status: VideoStatus
    message: str