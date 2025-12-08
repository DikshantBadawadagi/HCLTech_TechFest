class VideoAnalysisException(Exception):
    """Base exception for video analysis errors"""
    def __init__(self, message: str, status_code: int = 400, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class VideoUploadException(VideoAnalysisException):
    """Exception for video upload errors"""
    pass

class VideoProcessingException(VideoAnalysisException):
    """Exception for video processing errors"""
    pass

class TranscriptionException(VideoAnalysisException):
    """Exception for transcription errors"""
    pass

class AnalysisException(VideoAnalysisException):
    """Exception for analysis errors"""
    pass

class DatabaseException(VideoAnalysisException):
    """Exception for database operations"""
    pass