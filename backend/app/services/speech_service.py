import logging
from typing import Tuple, Optional
from app.config import settings
import json
import os

logger = logging.getLogger(__name__)

class SpeechService:
    """Speech-to-text transcription using Groq Whisper with local fallback"""
    
    def __init__(self):
        self.use_groq = settings.USE_GROQ_WHISPER
        self.groq_client = None
        self.local_model = None
        
        # Log configuration
        logger.info("="*70)
        logger.info("🎙️ INITIALIZING SPEECH SERVICE")
        logger.info(f"   USE_GROQ_WHISPER: {self.use_groq}")
        logger.info(f"   GROQ_API_KEY length: {len(settings.GROQ_API_KEY) if settings.GROQ_API_KEY else 0}")
        logger.info(f"   GROQ_API_KEY set: {bool(settings.GROQ_API_KEY)}")
        if settings.GROQ_API_KEY:
            logger.info(f"   API Key preview: {settings.GROQ_API_KEY[:15]}...{settings.GROQ_API_KEY[-5:]}")
        else:
            logger.warning(f"   ⚠️ GROQ_API_KEY is EMPTY - using from: {os.environ.get('GROQ_API_KEY', 'NOT IN ENV')}")
        logger.info(f"   GROQ_WHISPER_MODEL: {settings.GROQ_WHISPER_MODEL}")
        logger.info("="*70)
        
        # Initialize Groq if enabled and API key provided
        if self.use_groq and settings.GROQ_API_KEY:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
                logger.info(f"✅ Groq Whisper initialized with model: {settings.GROQ_WHISPER_MODEL}")
                logger.info(f"   Ready for cloud-based transcription!")
            except ImportError:
                logger.warning("⚠️ Groq library not installed. Falling back to local Whisper.")
                self.use_groq = False
            except Exception as e:
                logger.warning(f"⚠️ Groq initialization failed: {e}. Will use local Whisper fallback.")
                self.use_groq = False
        elif self.use_groq:
            logger.warning("⚠️ Groq enabled but GROQ_API_KEY not set. Will use local Whisper fallback.")
            logger.warning(f"   Debug: GROQ_API_KEY='{settings.GROQ_API_KEY}' (empty={not settings.GROQ_API_KEY})")
            self.use_groq = False
        else:
            logger.info("ℹ️ Groq disabled. Using local Whisper.")
        
        # Load local Whisper model as fallback
        if not self.use_groq or not self.groq_client:
            logger.info(f"📥 Loading local Whisper model as fallback: {settings.WHISPER_MODEL}")
            try:
                import whisper
                self.local_model = whisper.load_model(settings.WHISPER_MODEL)
                logger.info(f"✅ Local Whisper model loaded: {settings.WHISPER_MODEL}")
                logger.info(f"   Available as fallback if Groq fails!")
            except Exception as e:
                logger.error(f"❌ Failed to load local Whisper: {e}")
                logger.error(f"   This is critical - both Groq AND local Whisper are unavailable!")
                raise
    
    async def transcribe(self, audio_path: str) -> Tuple[str, float]:
        """
        Transcribe audio to text using Groq API with fallback to local Whisper
        
        Returns:
            Tuple of (transcript text, confidence score)
        """
        logger.info("🎤 Transcription request received")
        
        # Determine which service to use
        service_name = "GROQ CLOUD" if (self.use_groq and self.groq_client) else "LOCAL WHISPER"
        logger.info(f"   🔊 Using: {service_name}")
        
        if self.use_groq and self.groq_client:
            return await self._transcribe_groq(audio_path)
        else:
            return await self._transcribe_local(audio_path)
    
    async def _transcribe_groq(self, audio_path: str) -> Tuple[str, float]:
        """
        Transcribe using Groq Cloud Whisper API
        Falls back to local if rate limited or fails
        """
        try:
            logger.info(f"🌐 Groq: Starting transcription via cloud API")
            logger.info(f"   Audio file: {audio_path}")
            logger.info(f"   Model: {settings.GROQ_WHISPER_MODEL}")
            
            # Open audio file
            with open(audio_path, "rb") as audio_file:
                logger.info(f"📤 Sending audio to Groq API...")
                
                # Call Groq Whisper API
                transcription = self.groq_client.audio.transcriptions.create(
                    file=(audio_path.split("/")[-1], audio_file, "audio/wav"),
                    model=settings.GROQ_WHISPER_MODEL,
                    language="en",
                    temperature=0.0
                )
                
                transcript = transcription.text.strip()
                logger.info(f"✅ Groq transcription successful!")
                logger.info(f"   Length: {len(transcript)} chars")
                
                # Groq doesn't provide confidence scores, use high confidence as default
                confidence = 0.95
                
                return transcript, confidence
        
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check for specific errors
            if "401" in str(e) or "authentication" in error_msg or "invalid api key" in error_msg:
                logger.error(f"❌ Groq authentication failed (401): Invalid API key")
                logger.error(f"   Please check GROQ_API_KEY in .env file")
                logger.error(f"   Full error: {e}")
            elif "rate_limit" in error_msg or "429" in error_msg or "quota" in error_msg:
                logger.warning(f"⚠️ Groq rate limit hit: {e}")
            else:
                logger.error(f"❌ Groq API error: {e}")
            
            logger.warning(f"🔄 Falling back to local Whisper...")
            
            # Fallback to local Whisper
            return await self._transcribe_local(audio_path)
    
    async def _transcribe_local(self, audio_path: str) -> Tuple[str, float]:
        """
        Transcribe using local Whisper model (fallback)
        """
        try:
            if not self.local_model:
                raise RuntimeError("Local Whisper model not loaded")
            
            logger.info(f"🖥️ Local Whisper: Starting transcription")
            logger.info(f"   Audio file: {audio_path}")
            logger.info(f"   Model: {settings.WHISPER_MODEL}")
            
            # Transcribe with local Whisper
            result = self.local_model.transcribe(
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
            
            logger.info(f"✅ Local Whisper transcription successful!")
            logger.info(f"   Length: {len(transcript)} chars")
            logger.info(f"   Confidence: {round(avg_confidence, 3)}")
            
            return transcript, round(avg_confidence, 3)
        
        except Exception as e:
            logger.error(f"❌ Local Whisper transcription failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise