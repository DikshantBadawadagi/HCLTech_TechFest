from fastapi import UploadFile
import logging
import time
from datetime import datetime
import asyncio
from app.services.video_processor import VideoProcessor
from app.services.speech_service import SpeechService
from app.services.audio_service import AudioService
from app.services.nlp_service import NLPService
from app.services.visual_service import VisualService
from app.services.ocr_service import OCRService
from app.services.gemini_service import GeminiService
from app.services.scoring_service import ScoringService
from app.utils.file_handler import FileHandler
from app.utils.db_helper import get_database
from app.models.schemas import AnalysisResult, VideoStatus
from app.core.exceptions import VideoUploadException
from bson import ObjectId

logger = logging.getLogger(__name__)

class CompleteAnalysisController:
    """Single endpoint to upload and analyze video completely"""
    
    def __init__(self):
        self.file_handler = FileHandler()
        self.video_processor = VideoProcessor()
        self.speech_service = SpeechService()
        self.audio_service = AudioService()
        self.nlp_service = NLPService()
        self.visual_service = VisualService()
        self.ocr_service = OCRService()
        self.gemini_service = GeminiService()
        self.scoring_service = ScoringService()
    
    async def upload_and_analyze(
        self, 
        file: UploadFile,
        context: str = None
    ) -> AnalysisResult:
        """
        Upload video and perform complete analysis in one call
        Returns complete results immediately
        """
        db = get_database()
        start_time = time.time()
        
        try:
            # Step 1: Upload and validate video
            logger.info(f"📤 Uploading video: {file.filename}")
            self.file_handler.validate_video_file(file)
            file_path = await self.file_handler.save_upload_file(file)
            duration = self.file_handler.get_video_duration(file_path)
            
            import os
            file_size = os.path.getsize(file_path)
            
            # Save to database
            video_doc = {
                "filename": file.filename,
                "file_path": file_path,
                "size": file_size,
                "duration": duration,
                "status": VideoStatus.PROCESSING,
                "uploaded_at": datetime.utcnow()
            }
            
            result = await db.videos.insert_one(video_doc)
            video_id = str(result.inserted_id)
            
            logger.info(f"✅ Video uploaded: {video_id}")
            
            # Step 2: Run complete analysis
            logger.info(f"🔍 Starting analysis pipeline...")
            
            # Extract audio and keyframes
            audio_path, keyframes = await self.video_processor.process_video(file_path)
            
            # Transcribe
            transcript, confidence = await self.speech_service.transcribe(audio_path)
            
            # Parallel analysis
            results = await asyncio.gather(
                self.audio_service.analyze_audio(audio_path, transcript),
                self.nlp_service.analyze_engagement(transcript),
                self.gemini_service.analyze_technical_depth(transcript, context),
                self.visual_service.analyze_video(file_path),
                self.ocr_service.extract_text_from_frames(keyframes),
                return_exceptions=True
            )
            
            audio_metrics = results[0] if not isinstance(results[0], Exception) else {}
            engagement_data = results[1] if not isinstance(results[1], Exception) else {}
            technical_data = results[2] if not isinstance(results[2], Exception) else {}
            visual_data = results[3] if not isinstance(results[3], Exception) else {}
            
            # Calculate scores
            scores = self.scoring_service.calculate_scores(
                audio_metrics=audio_metrics,
                engagement_data=engagement_data,
                technical_data=technical_data,
                visual_data=visual_data,
                transcript=transcript
            )
            
            processing_time = time.time() - start_time
            
            # Create analysis document
            analysis_doc = {
                "video_id": video_id,
                "status": VideoStatus.COMPLETED,
                "context": context,
                "transcript": transcript,
                "transcript_confidence": confidence,
                "communication": scores["communication"].dict(),
                "engagement": scores["engagement"].dict(),
                "technical_depth": scores["technical_depth"].dict(),
                "clarity": scores["clarity"].dict(),
                "interaction": scores["interaction"].dict(),
                "overall_score": scores["overall"],
                "processing_time": round(processing_time, 2),
                "created_at": datetime.utcnow(),
                "completed_at": datetime.utcnow()
            }
            
            # Save to database
            analysis_result = await db.analysis_results.insert_one(analysis_doc)
            analysis_id = str(analysis_result.inserted_id)
            
            # Update video status
            await db.videos.update_one(
                {"_id": ObjectId(video_id)},
                {"$set": {"status": VideoStatus.COMPLETED}}
            )
            
            logger.info(f"✅ Analysis completed in {processing_time:.2f}s")
            
            # Return complete result
            return AnalysisResult(
                analysis_id=analysis_id,
                video_id=video_id,
                status=VideoStatus.COMPLETED,
                transcript=transcript,
                transcript_confidence=confidence,
                communication=scores["communication"],
                engagement=scores["engagement"],
                technical_depth=scores["technical_depth"],
                clarity=scores["clarity"],
                interaction=scores["interaction"],
                overall_score=scores["overall"],
                processing_time=round(processing_time, 2),
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
        
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Save error to database
            if 'video_id' in locals():
                await db.videos.update_one(
                    {"_id": ObjectId(video_id)},
                    {"$set": {"status": VideoStatus.FAILED}}
                )
                
                error_doc = {
                    "video_id": video_id,
                    "status": VideoStatus.FAILED,
                    "error_message": str(e),
                    "created_at": datetime.utcnow(),
                    "completed_at": datetime.utcnow()
                }
                
                analysis_result = await db.analysis_results.insert_one(error_doc)
                analysis_id = str(analysis_result.inserted_id)
                
                return AnalysisResult(
                    analysis_id=analysis_id,
                    video_id=video_id,
                    status=VideoStatus.FAILED,
                    transcript="",
                    transcript_confidence=0.0,
                    communication=None,
                    engagement=None,
                    technical_depth=None,
                    clarity=None,
                    interaction=None,
                    overall_score=0.0,
                    processing_time=time.time() - start_time,
                    created_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    error_message=str(e)
                )
            else:
                raise VideoUploadException(f"Failed to process video: {str(e)}")
    
    async def get_analysis_by_id(self, analysis_id: str) -> AnalysisResult:
        """Get analysis results by analysis ID"""
        db = get_database()
        
        result = await db.analysis_results.find_one({"_id": ObjectId(analysis_id)})
        
        if not result:
            return None
        
        return self._format_result(result)
    
    async def get_analysis_by_video_id(self, video_id: str) -> AnalysisResult:
        """Get analysis results by video ID"""
        db = get_database()
        
        result = await db.analysis_results.find_one({"video_id": video_id})
        
        if not result:
            return None
        
        return self._format_result(result)
    
    def _format_result(self, doc: dict) -> AnalysisResult:
        """Format database document to AnalysisResult"""
        from app.models.schemas import (
            CommunicationMetrics, EngagementMetrics, TechnicalDepthMetrics,
            ClarityMetrics, InteractionMetrics
        )
        
        communication = None
        if doc.get("communication"):
            communication = CommunicationMetrics(**doc["communication"])
        
        engagement = None
        if doc.get("engagement"):
            engagement = EngagementMetrics(**doc["engagement"])
        
        technical_depth = None
        if doc.get("technical_depth"):
            technical_depth = TechnicalDepthMetrics(**doc["technical_depth"])
        
        clarity = None
        if doc.get("clarity"):
            clarity = ClarityMetrics(**doc["clarity"])
        
        interaction = None
        if doc.get("interaction"):
            interaction = InteractionMetrics(**doc["interaction"])
        
        return AnalysisResult(
            analysis_id=str(doc["_id"]),
            video_id=doc["video_id"],
            status=VideoStatus(doc["status"]),
            transcript=doc.get("transcript", ""),
            transcript_confidence=doc.get("transcript_confidence", 0.0),
            communication=communication,
            engagement=engagement,
            technical_depth=technical_depth,
            clarity=clarity,
            interaction=interaction,
            overall_score=doc.get("overall_score", 0.0),
            processing_time=doc.get("processing_time", 0.0),
            created_at=doc["created_at"],
            completed_at=doc.get("completed_at"),
            error_message=doc.get("error_message")
        )