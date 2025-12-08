import whisper
import logging
from typing import Tuple
from app.config import settings

logger = logging.getLogger(__name__)

class SpeechService:
    """Speech-to-text transcription using Whisper"""
    
    def __init__(self):
        logger.info(f"Loading Whisper model: {settings.WHISPER_MODEL}")
        self.model = whisper.load_model(settings.WHISPER_MODEL)
    
    async def transcribe(self, audio_path: str) -> Tuple[str, float]:
        """
        Transcribe audio to text
        
        Returns:
            Tuple of (transcript text, average confidence)
        """
        try:
            logger.info(f"Transcribing audio: {audio_path}")
            
            # Transcribe
            result = self.model.transcribe(
                audio_path,
                language='en',
                task='transcribe',
                verbose=False
            )
            
            transcript = result['text'].strip()
            
            # Calculate average confidence from segments
            segments = result.get('segments', [])
            if segments:
                avg_confidence = sum(seg.get('no_speech_prob', 0) for seg in segments) / len(segments)
                avg_confidence = 1 - avg_confidence  # Convert to confidence
            else:
                avg_confidence = 0.0
            
            logger.info(f"Transcription complete. Length: {len(transcript)} chars")
            return transcript, round(avg_confidence, 3)
        
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            raise