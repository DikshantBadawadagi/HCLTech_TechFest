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
        Transcribe using Groq Cloud Whisper API with chunking for large files
        """
        try:
            logger.info(f"🌐 Groq: Starting transcription via cloud API")
            logger.info(f"   Audio file: {audio_path}")
            logger.info(f"   Model: {settings.GROQ_WHISPER_MODEL}")
            
            # Check file size
            file_size = os.path.getsize(audio_path)
            logger.info(f"   File size: {file_size / (1024*1024):.2f} MB")
            
            # If under 20MB, send directly
            if file_size < 20 * 1024 * 1024:
                with open(audio_path, "rb") as audio_file:
                    logger.info(f"📤 Sending audio to Groq API (direct)...")
                    transcription = self.groq_client.audio.transcriptions.create(
                        file=(audio_path.split("/")[-1], audio_file, "audio/wav"),
                        model=settings.GROQ_WHISPER_MODEL,
                        language="en",
                        temperature=0.0
                    )
                    transcript = transcription.text.strip()
                    logger.info(f"✅ Groq transcription successful!")
                    logger.info(f"   Length: {len(transcript)} chars")
                    confidence = 0.95
                    return transcript, confidence
            else:
                # Chunk large files
                logger.info(f"📦 File too large, chunking into segments...")
                return await self._transcribe_groq_chunked(audio_path)
        
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
    
    async def _transcribe_groq_chunked(self, audio_path: str) -> Tuple[str, float]:
        """
        Split large audio into smaller chunks for ultra-fast processing
        MP3 + 8-10 second chunks = minimal file size + quick requests
        """
        import librosa
        import soundfile as sf
        import tempfile
        
        try:
            logger.info("📦 Loading audio for chunking...")
            # Load at 16kHz (already optimized by extract_audio)
            y, sr = librosa.load(audio_path, sr=16000)
            duration = len(y) / sr
            logger.info(f"   Audio duration: {duration:.1f}s at {sr}Hz")
            
            # Ultra-short chunks = fastest processing
            # 8 seconds per chunk (vs 30s before)
            # Groq processes these instantly with no rate limits
            chunk_duration = 8  # seconds
            chunk_samples = int(chunk_duration * sr)
            
            chunks_list = []
            temp_files = []
            
            for i in range(0, len(y), chunk_samples):
                chunk = y[i:i+chunk_samples]
                chunks_list.append(chunk)
            
            logger.info(f"   Split into {len(chunks_list)} chunks ({chunk_duration}s each)")
            
            all_transcripts = []
            
            for idx, chunk in enumerate(chunks_list):
                logger.info(f"📤 Transcribing chunk {idx+1}/{len(chunks_list)}...")
                
                # Save chunk to temp file as MP3 for ultra-compression
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                    # Convert to MP3 using librosa -> PCM -> save as MP3
                    # But actually, let's keep as WAV and let ffmpeg compress later
                    # For now, save as WAV for compatibility
                    sf.write(tmp.name, chunk, sr, subtype='PCM_16')
                    temp_files.append(tmp.name)
                    
                    # Check file size
                    chunk_size_kb = os.path.getsize(tmp.name) / 1024
                    logger.info(f"   Chunk size: {chunk_size_kb:.1f} KB")
                    
                    # Transcribe chunk
                    with open(tmp.name, 'rb') as chunk_file:
                        transcription = self.groq_client.audio.transcriptions.create(
                            file=(f"chunk_{idx}.wav", chunk_file, "audio/wav"),
                            model=settings.GROQ_WHISPER_MODEL,
                            language="en",
                            temperature=0.0
                        )
                        all_transcripts.append(transcription.text.strip())
                        logger.info(f"   ✅ Chunk {idx+1} done")
            
            # Combine all transcripts
            full_transcript = " ".join(all_transcripts)
            logger.info(f"✅ Chunked transcription complete!")
            logger.info(f"   Total length: {len(full_transcript)} chars")
            
            # Cleanup temp files
            for tmp_file in temp_files:
                try:
                    os.remove(tmp_file)
                except:
                    pass
            
            return full_transcript, 0.95
        
        except Exception as e:
            logger.error(f"❌ Chunked transcription failed: {e}")
            raise
    
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