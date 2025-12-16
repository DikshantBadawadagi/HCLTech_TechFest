# from pydantic_settings import BaseSettings
# from typing import Optional

# class Settings(BaseSettings):
#     # MongoDB
#     MONGO_URI: str = "mongodb://admin:admin123@mongo:27017/"
#     DB_NAME: str = "teacher_analysis"
    
#     # File Storage
#     UPLOAD_FOLDER: str = "/app/data/uploads"
#     MAX_VIDEO_SIZE: int = 500 * 1024 * 1024  # 500MB
#     ALLOWED_EXTENSIONS: set = {".mp4", ".avi", ".mov", ".mkv"}
    
#     # Model Configuration
#     WHISPER_MODEL: str = "base"  # tiny, base, small, medium, large
#     SENTENCE_TRANSFORMER_MODEL: str = "all-MiniLM-L6-v2"
    
#     # Processing
#     KEYFRAME_INTERVAL: int = 30  # Extract 1 frame every 30 frames
#     AUDIO_SAMPLE_RATE: int = 16000
    
#     # Scoring Weights
#     WEIGHT_ENGAGEMENT: float = 0.20
#     WEIGHT_COMMUNICATION: float = 0.20
#     WEIGHT_TECHNICAL_DEPTH: float = 0.30
#     WEIGHT_CLARITY: float = 0.20
#     WEIGHT_INTERACTION: float = 0.10
    
#     class Config:
#         env_file = ".env"

# settings = Settings()

from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # MongoDB
    MONGO_URI: str = "mongodb://admin:admin123@mongo:27017/"
    DB_NAME: str = "teacher_analysis"
    
    # File Storage
    UPLOAD_FOLDER: str = "/app/data/uploads"
    MAX_VIDEO_SIZE: int = 500 * 1024 * 1024  # 500MB
    ALLOWED_EXTENSIONS: set = {".mp4", ".avi", ".mov", ".mkv"}
    
    # Model Configuration
    WHISPER_MODEL: str = "tiny"  # Changed from "base" to "tiny" for speed
    SENTENCE_TRANSFORMER_MODEL: str = "all-MiniLM-L6-v2"
    
    # Gemini API (for Technical Depth Analysis)
    GEMINI_API_KEY: str = ""  # Set via environment variable
    GEMINI_MODEL: str = "gemini-1.5-flash"  # Fast and efficient
    
    # Groq Whisper API (Cloud-based Speech-to-Text with fallback)
    GROQ_API_KEY: str = ""  # Set via environment variable
    GROQ_WHISPER_MODEL: str = "whisper-large-v3"  # Larger model for better accuracy
    USE_GROQ_WHISPER: bool = True  # Enable Groq Whisper (falls back to local if disabled)
    GROQ_REQUEST_TIMEOUT: int = 60  # Timeout in seconds
    
    # Processing
    KEYFRAME_INTERVAL: int = 60  # Changed from 30 to 60 (half the frames)
    AUDIO_SAMPLE_RATE: int = 16000
    
    # Scoring Weights
    WEIGHT_ENGAGEMENT: float = 0.20
    WEIGHT_COMMUNICATION: float = 0.20
    WEIGHT_TECHNICAL_DEPTH: float = 0.30
    WEIGHT_CLARITY: float = 0.20
    WEIGHT_INTERACTION: float = 0.10
    
    # Performance Settings
    ENABLE_PARALLEL_PROCESSING: bool = True
    MAX_VIDEO_DURATION: int = 3600  # 1 hour max
    
    class Config:
        # In Docker: env_file from docker-compose is injected as environment variables
        # In local dev: load from .env file if it exists
        env_file = ".env" if os.path.exists(".env") else None
        case_sensitive = False

settings = Settings()