import logging
import asyncio
import time
from typing import Dict
from app.services.video_processor import VideoProcessor
from app.services.speech_service import SpeechService
from app.services.audio_service import AudioService
from app.services.nlp_service import NLPService
from app.services.visual_service import VisualService
from app.config import settings

logger = logging.getLogger(__name__)

class ChunkAnalyzer:
    """
    Analyze a single video chunk without Gemini
    Optimized for parallel batch processing
    """
    
    def __init__(self):
        self.video_processor = VideoProcessor()
        self.speech_service = SpeechService()
        self.audio_service = AudioService()
        self.nlp_service = NLPService()
        self.visual_service = VisualService()
    
    async def analyze_chunk(self, video_path: str, chunk_id: str) -> Dict:
        """
        Analyze a single chunk completely
        
        Returns dict with all analysis results
        """
        start_time = time.time()
        
        try:
            logger.info(f"[Chunk {chunk_id}] Starting analysis")
            
            # Step 1: Extract audio and keyframes
            logger.info(f"[Chunk {chunk_id}] Extracting audio/keyframes")
            audio_path, keyframes = await self.video_processor.process_video(video_path)
            
            # Step 2: Transcribe audio (slowest operation)
            logger.info(f"[Chunk {chunk_id}] Transcribing...")
            transcript, confidence = await self.speech_service.transcribe(audio_path)
            
            # Step 3: Run parallel analysis (audio, NLP, visual)
            logger.info(f"[Chunk {chunk_id}] Running parallel analysis")
            
            results = await asyncio.gather(
                self.audio_service.analyze_audio(audio_path, transcript),
                self.nlp_service.analyze_engagement(transcript),
                self.visual_service.analyze_video(video_path),
                return_exceptions=True
            )
            
            audio_metrics = results[0] if not isinstance(results[0], Exception) else self._default_audio_metrics()
            engagement_data = results[1] if not isinstance(results[1], Exception) else self._default_engagement()
            visual_data = results[2] if not isinstance(results[2], Exception) else self._default_visual()
            
            # Log any failures
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"[Chunk {chunk_id}] Analysis task {i} failed: {result}")
            
            # Step 4: Calculate scores (no technical depth)
            logger.info(f"[Chunk {chunk_id}] Calculating scores")
            scores = self._calculate_chunk_scores(
                audio_metrics, 
                engagement_data, 
                visual_data, 
                transcript
            )
            
            processing_time = time.time() - start_time
            
            logger.info(f"[Chunk {chunk_id}] ✅ Completed in {processing_time:.2f}s")
            
            return {
                "status": "success",
                "transcript": transcript,
                "transcript_confidence": confidence,
                "audio_metrics": audio_metrics,
                "engagement_data": engagement_data,
                "visual_data": visual_data,
                "scores": scores,
                "processing_time": processing_time
            }
        
        except Exception as e:
            logger.error(f"[Chunk {chunk_id}] ❌ Failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {
                "status": "failed",
                "error": str(e),
                "processing_time": time.time() - start_time
            }
    
    def _calculate_chunk_scores(
        self, 
        audio_metrics: Dict, 
        engagement_data: Dict, 
        visual_data: Dict,
        transcript: str
    ) -> Dict:
        """
        Calculate scores without technical depth (no Gemini)
        Adjust weights: Communication 25%, Engagement 25%, Clarity 30%, Interaction 20%
        """
        
        # Communication Score
        comm_score = self._calculate_communication(audio_metrics)
        
        # Engagement Score
        eng_score = self._calculate_engagement(engagement_data)
        
        # Clarity Score
        clarity_score = self._calculate_clarity(audio_metrics, visual_data)
        
        # Interaction Score
        interaction_score = self._calculate_interaction(visual_data)
        
        # Overall (no technical depth)
        overall = (
            comm_score * 0.25 +
            eng_score * 0.25 +
            clarity_score * 0.30 +
            interaction_score * 0.20
        )
        
        return {
            "communication": comm_score,
            "engagement": eng_score,
            "clarity": clarity_score,
            "interaction": interaction_score,
            "overall": round(overall, 2)
        }
    
    def _calculate_communication(self, audio_metrics: Dict) -> float:
        """Communication score from audio metrics"""
        speaking_rate = audio_metrics["speaking_rate"]
        pause_count = audio_metrics["pause_count"]
        stuttering_count = audio_metrics["stuttering_count"]
        volume_std = audio_metrics["volume_std"]
        pitch_std = audio_metrics["pitch_std"]
        
        # Speaking rate score (optimal: 130-170 WPM)
        if 130 <= speaking_rate <= 170:
            rate_score = 1.0
        elif 100 <= speaking_rate < 130 or 170 < speaking_rate <= 200:
            rate_score = 0.7
        else:
            rate_score = 0.4
        
        pause_score = 1.0 if 5 <= pause_count <= 20 else 0.6
        stutter_score = max(0, 1.0 - (stuttering_count * 0.1))
        volume_score = min(1.0, volume_std * 10)
        pitch_score = min(1.0, pitch_std / 50)
        
        score = (
            rate_score * 0.3 +
            pause_score * 0.2 +
            stutter_score * 0.2 +
            volume_score * 0.15 +
            pitch_score * 0.15
        ) * 100
        
        return round(score, 2)
    
    def _calculate_engagement(self, engagement_data: Dict) -> float:
        """Engagement score from NLP analysis"""
        qna_pairs = engagement_data["qna_pairs"]
        question_count = engagement_data["question_count"]
        interaction_moments = engagement_data["interaction_moments"]
        rhetorical_questions = engagement_data.get("rhetorical_questions", 0)
        direct_address_count = engagement_data.get("direct_address_count", 0)
        
        qna_score = min(1.0, qna_pairs / 10)
        question_score = min(1.0, question_count / 15)
        interaction_score = min(1.0, interaction_moments / 20)
        rhetorical_score = min(1.0, rhetorical_questions / 5)
        direct_address_score = min(1.0, direct_address_count / 30)
        
        score = (
            qna_score * 0.25 +
            question_score * 0.20 +
            interaction_score * 0.25 +
            rhetorical_score * 0.15 +
            direct_address_score * 0.15
        ) * 100
        
        return round(score, 2)
    
    def _calculate_clarity(self, audio_metrics: Dict, visual_data: Dict) -> float:
        """Clarity score from audio and video quality"""
        video_quality = visual_data["video_quality_score"]
        volume_mean = audio_metrics["volume_mean"]
        pitch_std = audio_metrics["pitch_std"]
        eye_contact = visual_data["eye_contact_percentage"]
        
        audio_quality = min(1.0, volume_mean * 100)
        energy_score = min(1.0, volume_mean * 50)
        pitch_variation = min(1.0, pitch_std / 50)
        eye_contact_score = eye_contact / 100
        
        score = (
            video_quality * 0.25 +
            audio_quality * 0.25 +
            energy_score * 0.2 +
            pitch_variation * 0.15 +
            eye_contact_score * 0.15
        ) * 100
        
        return round(score, 2)
    
    def _calculate_interaction(self, visual_data: Dict) -> float:
        """Interaction score from visual analysis"""
        eye_contact = visual_data["eye_contact_percentage"]
        gesture_frequency = visual_data["gesture_frequency"]
        pose_stability = visual_data["pose_stability"]
        
        eye_contact_score = eye_contact / 100
        gesture_score = 1.0 if 3 <= gesture_frequency <= 8 else 0.6
        
        score = (
            eye_contact_score * 0.5 +
            gesture_score * 0.3 +
            pose_stability * 0.2
        ) * 100
        
        return round(score, 2)
    
    def _default_audio_metrics(self) -> Dict:
        """Default audio metrics if analysis fails"""
        return {
            "speaking_rate": 150.0,
            "pause_count": 10,
            "avg_pause_duration": 1.0,
            "stuttering_count": 0,
            "volume_mean": 0.05,
            "volume_std": 0.01,
            "pitch_mean": 200.0,
            "pitch_std": 30.0
        }
    
    def _default_engagement(self) -> Dict:
        """Default engagement if analysis fails"""
        return {
            "qna_pairs": 0,
            "question_count": 0,
            "interaction_moments": 0,
            "rhetorical_questions": 0,
            "direct_address_count": 0
        }
    
    def _default_visual(self) -> Dict:
        """Default visual metrics if analysis fails"""
        return {
            "eye_contact_percentage": 50.0,
            "gesture_frequency": 5.0,
            "pose_stability": 0.7,
            "video_quality_score": 0.5
        }